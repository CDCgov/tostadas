
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
        lift_signal
        vadr_signal
        val_signal
        valMeta
        lifted_Fasta
        lifted_Gff
        entry_flag
    main:
    
        valMeta = Channel.fromPath('params.val_output_dir/*/tsv_per_sample/*.tsv')
        lifted_Gff = Channel.fromPath('final_liftoff_output_dir/*/liftoff/*.gff')
        lifted_Fasta = Channel.fromPath('final_liftoff_output_dir/*/fasta/*.fasta')
    
        SUBMISSION ( lift_signal, vadr_signal, val_signal, valMeta, lifted_Fasta, lifted_Gff, entry_flag)

        GET_WAIT_TIME ( SUBMISSION.out, valMeta, entry_flag )

        WAIT ( GET_WAIT_TIME.out[0], GET_WAIT_TIME.out[1] )

        UPDATE_SUBMISSION ( WAIT.out )
}
