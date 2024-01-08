/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN VADR ANNOTATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process VADR {

    label 'vadr'

    errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
    maxRetries 5
    
    try {
        container "$params.docker_container_vadr"
    } catch (Exception e) {
        System.err.println("WARNING: Cannot pull the following docker container: $params.docker_container_vadr to run VADR")
    }

    input:
    val signal
    path fasta_path
    path vadr_models_dir

    script:
    """
    VADRMODELDIR=$vadr_models_dir && \
    v-annotate.pl --split --cpu 8 --glsearch --minimap2 -s -r --nomisc \
    --r_lowsimok --r_lowsimxd 100 --r_lowsimxl 2000 --alt_pass \
    discontn,dupregin --s_overhang 150 -i $vadr_models_dir/mpxv.rpt.minfo -n \
    $vadr_models_dir/mpxv.fa -x $vadr_models_dir $fasta_path \
    original_outputs -f
    """

    output:
    path "original_outputs", emit: vadr_outputs
}