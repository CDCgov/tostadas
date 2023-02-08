// get the utility processes
include { VALIDATE_PARAMS } from "$projectDir/nf_modules/utility_mods"
include { CLEANUP_FILES } from "$projectDir/nf_modules/utility_mods"
include { WAIT } from "$projectDir/nf_modules/utility_mods"
include { SUBMISSION_ENTRY_CHECK } from "$projectDir/nf_modules/utility_mods"

// get the main processes
include { METADATA_VALIDATION } from "$projectDir/nf_modules/main_mods"
include { LIFTOFF } from "$projectDir/nf_modules/main_mods"
include { VADR } from "$projectDir/nf_modules/main_mods"
include { SUBMISSION } from "$projectDir/nf_modules/main_mods"
include { UPDATE_SUBMISSION } from "$projectDir/nf_modules/main_mods"

// get the subworkflows
include { RUN_SUBMISSION } from "$projectDir/nf_subworkflows/submission"
include { RUN_UTILITY } from "$projectDir/nf_subworkflows/utility"


workflow WITH_SUBMISSION {
    take:
        cleanup_signal
        meta
        fasta
        ref_fasta
        ref_gff
        valMeta
        lifted_Gff
        lifted_Fasta
        
    main:      
        meta = Channel.fromPath(params.meta_path)
        fasta = Channel.fromPath(params.fasta_path)
        ref_fasta = Channel.fromPath(params.ref_fasta_path)
        ref_gff = Channel.fromPath(params.ref_gff_path)
        valMeta = Channel.fromPath('params.val_output_dir/*/tsv_per_sample/*.tsv')
        lifted_Gff = Channel.fromPath('final_liftoff_output_dir/*/liftoff/*.gff')
        lifted_Fasta = Channel.fromPath('final_liftoff_output_dir/*/fasta/*.fasta')
        
        // run cleanup
        RUN_UTILITY()
        
        // run metadata validation
        METADATA_VALIDATION ( cleanup_signal, meta, fasta)

        // run annotation (in parallel)
        if ( params.run_liftoff == true ) {
            LIFTOFF ( cleanup_signal, meta, fasta, ref_fasta, ref_gff )
        }
        if ( params.run_vadr == true ) {
            VADR ( cleanup_signal, channels['fasta'] )
        }

        // run post annotation checks
        if ( params.run_liftoff == true ) {
            RUN_SUBMISSION ( LIFTOFF.out[1], false, METADATA_VALIDATION.out[1], true,
            valMeta,
            lifted_Gff,
            lifted_Fasta
            )

        } else if ( params.run_vadr == true ) {
            RUN_SUBMISSION ( 'dummy signal', VADR.out[1], METADATA_VALIDATION.out[1], false,
            "$params.output_dir/$params.val_output_dir",
            "$params.output_dir/$params.final_liftoff_output_dir",
            "$params.output_dir/$params.final_liftoff_output_dir"
            )

        } else if ( params.run_vadr == true && params.run_liftoff == true ) {
            RUN_SUBMISSION ( LIFTOFF.out[1], VADR.out[1], METADATA_VALIDATION.out[1], false,
            "$params.output_dir/$params.val_output_dir",
            "$params.output_dir/$params.final_liftoff_output_dir",
            "$params.output_dir/$params.final_liftoff_output_dir"
            )
        }
}
