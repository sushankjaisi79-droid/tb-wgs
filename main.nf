params {
    // CSV with columns: sample_id, fastq_1, fastq_2
    samplesheet: String = 'assets/samplesheet.csv'
    // PREVISGEN-TB release; changing it regenerates all reports
    version: String = '0.1.0'
}

process TBPROFILER {
    tag "${sample_id}"
    cpus 8

    input:
    tuple val(sample_id), path(fastq_1), path(fastq_2)

    output:
    tuple val(sample_id), path("${sample_id}.results.json"), path("${sample_id}.results.txt")

    script:
    """
    tb-profiler profile -1 ${fastq_1} -2 ${fastq_2} -t ${task.cpus} -p ${sample_id} --txt
    mv results/${sample_id}.results.json results/${sample_id}.results.txt .
    """
}

process QC_GATE {
    tag "${sample_id}"
    cpus 1

    input:
    tuple val(sample_id), path(json), path(txt)

    output:
    tuple val(sample_id), path("${sample_id}.qc.json")

    script:
    """
    qc_gate.py ${json} --outdir .
    """
}

process REPORT {
    tag "${sample_id}"
    cpus 1

    input:
    tuple val(sample_id), path(json), path(txt), path(qc)
    val version
    val script_md5

    output:
    path "${sample_id}.report.html"

    script:
    """
    # make_report.py ${script_md5}
    make_report.py sample --json ${json} --txt ${txt} --qc ${qc} --out ${sample_id}.report.html --version ${version}
    """
}

process REPORT_INDEX {
    cpus 1

    input:
    path files
    val version
    val script_md5

    output:
    path "index.html"

    script:
    """
    # make_report.py ${script_md5}
    make_report.py index ${files} --out index.html --version ${version}
    """
}

workflow {
    main:
    ch_reads = channel.fromPath(params.samplesheet)
        .splitCsv(header: true)
        .map { row -> tuple(row.sample_id, file(row.fastq_1), file(row.fastq_2)) }

    ch_profiles = TBPROFILER(ch_reads)
    ch_qc = QC_GATE(ch_profiles)
    ch_joined = ch_profiles.join(ch_qc)
    report_md5 = file("${projectDir}/bin/make_report.py").text.md5()
    ch_reports = REPORT(ch_joined, params.version, report_md5)
    ch_index = REPORT_INDEX(ch_joined.flatMap { _sid, j, _t, q -> [j, q] }.collect(), params.version, report_md5)

    publish:
    profiles = ch_profiles
    qc = ch_qc
    reports = ch_reports.mix(ch_index)
}

output {
    profiles {
        path 'tbprofiler'
    }
    qc {
        path 'qc'
    }
    reports {
        path 'reports'
    }
}
