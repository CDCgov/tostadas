//
// Check input samplesheet and get read channels
//

include { METADATA_CHECK } from '../../modules/local/samplesheet_check/main'

workflow INPUT_CHECK {
    take:
    //file samplesheet from samplesheet_to_check
    metadata // file: /path/to/samplesheet.csv

    main:
    METADATA_CHECK ( metadata )
        .csv
        .splitCsv ( header:true, sep:',' )
        .map { create_fasta_channel(it) }
        .map { create_fastq_channel(it) }
        .set { reads }

    emit:
    fasta                                     // channel: [ val(meta), [ fasta ] ]
    reads                                     // channel: [ val(meta), [ reads ] ]
    // versions = SAMPLESHEET_CHECK.out.versions // channel: [ versions.yml ]
}

    // Function to get list of [ meta, [ fasta ] ]
    def create_fasta_channel(LinkedHashMap row) {
        // create meta map
        def meta = [:]
        meta.id      = row.sequence

        // add path of the fasta file to the meta map
        def fasta_meta = []
        if (!file(row.fasta_path).exists()) {
            fasta_meta = [ meta, " " ]
        }
        fasta_meta = [ meta, file(row.fasta_path) ]

        return fasta_meta
    }
    // Function to get list of [ meta, [ fastq_1, fastq_2 ] ]
    def create_fastq_channel(LinkedHashMap row) {
        // create meta map
        def meta = [:]
        meta.id         = row.sample_name
        meta.single_end = row.single_end.toBoolean()

        // add path(s) of the fastq file(s) to the meta map
        def fastq_meta = []
        if (!file(row.illumina_sra_file_path_1).exists()) {
            fastq_meta = [ meta, [ file(row.illumina_sra_file_path_1), file(row.illumina_sra_file_path_1) ] ]
        }
        if (meta.single_end) {
            fastq_meta = [ meta, [ file(row.fastq_1) ] ]
        } else {
            if (!file(row.illumina_sra_file_path_2).exists()) {
                fastq_meta = [ meta, [ file(row.illumina_sra_file_path_1), file(row.illumina_sra_file_path_1) ] ]
            }
            fastq_meta = [ meta, [ file(row.illumina_sra_file_path_1), file(row.illumina_sra_file_path_1) ] ]
        }
        return fastq_meta
    }