/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                               RUNNING UTILITY FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { VALIDATE_PARAMS } from '../modules/general_util/validate_params/main'
include { CLEANUP_FILES } from '../modules/general_util/cleanup_files/main'

workflow RUN_UTILITY {
    
    main:
        VALIDATE_PARAMS()
        
        if ( params.cleanup == true ) {
            CLEANUP_FILES( VALIDATE_PARAMS.out )
        }

    emit:
        CLEANUP_FILES.out
}

