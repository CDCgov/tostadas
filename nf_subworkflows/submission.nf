/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { SUBMISSION } from '../nf_modules/main_mods'
include { UPDATE_SUBMISSION } from '../nf_modules/main_mods'
include { WAIT } from '../nf_modules/utility_mods'
include { GET_WAIT_TIME } from '../nf_modules/utility_mods'

workflow RUN_SUBMISSION {
    take:
        val lift_signal
        val vadr_signal
        val val_signal
        val validated_meta_path from valMeta
        val lifted_fasta_path from lifted_Fasta
        val lifted_gff_path from lifted_Gff
        val entry_flag
       
        
    main:
        SUBMISSION ( lift_signal, vadr_signal, val_signal, validated_meta_path, lifted_fasta_path, lifted_gff_path, entry_flag )

        GET_WAIT_TIME ( SUBMISSION.out, validated_meta_path, entry_flag )

        WAIT ( GET_WAIT_TIME.out[0], GET_WAIT_TIME.out[1] )

        UPDATE_SUBMISSION ( WAIT.out )
}
