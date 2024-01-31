/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                               RUNNING UTILITY FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { VALIDATE_PARAMS } from '../../modules/local/general_util/validate_params/main'
include { CLEANUP_FILES } from '../../modules/local/general_util/cleanup_files/main'

workflow RUN_UTILITY {
    
    main:
        // run validate params process always
        VALIDATE_PARAMS()
        
        // check if the cleanup param is set to true, if it is, run the process for it
        if ( params.cleanup == true ) {
            CLEANUP_FILES( VALIDATE_PARAMS.out )
        }

    emit:
        true 
}

