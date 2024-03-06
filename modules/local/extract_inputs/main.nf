process EXTRACT_INPUTS {
    input:
    file tsvFile

    output:
    tuple val(sequence_name), path(fasta, true), path(fastq_1, true), path(fastq_2, true) into samplesChannel

    script:
    """
    samples = file("${tsvFile}").readLines().drop(1).splitCsv(header: true, sep: '\t')

    def input_files = []

    samples.each { sample ->
        sequence_name = sample.sequence_name
        fasta = sample.containsKey('fasta_path') ? path(sample.fasta_path) : null
        fastq = sample.containsKey('sra-file_name') ? sample['sra-file_name'].split(',') : ['', '']
        fastq_1 = fastq[0] != '' ? path(fastq[0]) : null
        fastq_2 = fastq[1] != '' ? path(fastq[1]) : null
        input_files << tuple(sequence_name, fasta, fastq_1, fastq_2)
    }

    emit input_files
    """
}
