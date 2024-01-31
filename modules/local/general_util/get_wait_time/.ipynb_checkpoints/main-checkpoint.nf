process GET_WAIT_TIME {
    input:
        val validated_meta_path
    exec:
        if ( params.submission_wait_time != 'calc' ) {
            submission_wait_time = params.submission_wait_time
        } else {
            i = validated_meta_path.toList().size
            submission_wait_time = 3 * 60 * i
        }
    output:
        val submission_wait_time
}