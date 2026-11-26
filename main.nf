params {
    samplesheet: String = 'assets/samplesheet.csv'
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

workflow {
    main:
    ch_reads = channel.fromPath(params.samplesheet)
        .splitCsv(header: true)
        .map { row -> tuple(row.sample_id, file(row.fastq_1), file(row.fastq_2)) }

    ch_profiles = TBPROFILER(ch_reads)

    publish:
    profiles = ch_profiles
}

output {
    profiles {
        path 'tbprofiler'
    }
}
