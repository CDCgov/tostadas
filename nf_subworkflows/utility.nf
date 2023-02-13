/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                               RUNNING UTILITY FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { VALIDATE_PARAMS } from '../nf_modules/utility_mods'
include { CLEANUP_FILES } from '../nf_modules/utility_mods'

workflow RUN_UTILITY {
    
    main:
        VALIDATE_PARAMS()
        
        if ( params.cleanup == true ) {
            CLEANUP_FILES( VALIDATE_PARAMS.out )
        }

    emit:
        CLEANUP_FILES.out
}

