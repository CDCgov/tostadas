#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            REPEAT MASKER & LIFTOFF ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
// Channel
//     .fromPath(params.fasta_path)
//     .splitFasta( record: [id: true, seqString: true ])
//     .set { ch_fasta }

include { REPEATMASKER                                      } from "../modules/repeatmasker_annotation/main"
include { LIFTOFF_CLI                                       } from "../modules/liftoff_cli_annotation/main"
include { CONCAT_GFFS                                       } from "../modules/concat_gffs/main"

workflow RUN_REPEATMASKER_LIFTOFF {

    take:
        utility_signal 

    main:
        // run repeatmasker annotation on files
        REPEATMASKER (
           utility_signal ,
           params.fasta_path,
           params.repeat_lib
        )
        // run liftoff annotation on files
        LIFTOFF_CLI ( 
            utility_signal ,
            params.fasta_path,
            params.ref_fasta_path, 
            params.ref_gff_path 
        )
        // concat gffs
        CONCAT_GFFS (
           params.ref_gff_path,
           REPEATMASKER.out.gff,
           LIFTOFF_CLI.out.gff
        )

    emit:
        LIFTOFF_CLI.out.fasta.sort().flatten()
        CONCAT_GFFS.out.gff.sort().flatten()
}
