/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process PREP_SUBMISSION {

    conda(params.env_yml)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'docker.io/staphb/tostadas:latest' : 'docker.io/staphb/tostadas:latest' }"

    input:
    tuple val(meta), val(samples), val(enabledDatabases), path(batch_tsv), path(fastas, stageAs: 'fastas/*'), path(gffs, stageAs: 'gffs/*'), path(fq1s, stageAs: 'fq1s/*'), path(fq2s, stageAs: 'fq2s/*'), path(nnps, stageAs: 'nnps/*')
    path(submission_config)

    output:
    tuple val(meta), path("${meta.batch_id}"), emit: submission_files
    // Removed: path("${meta.batch_id}/prep_submission.log"), emit: submission_log, optional: true
    // On Nextflow's Google Batch executor, `optional: true` isn't fully
    // respected during output staging: staging attempts `mv` on the
    // declared file even when it doesn't exist, failing the task with
    // `mv: cannot stat '.../prep_submission.log'`. The log file (when
    // created by submission_prep.py) is still emitted as part of the
    // catch-all `path("${meta.batch_id}")` output above, so nothing
    // downstream needs the separate emit.

    when:
    "sra" in enabledDatabases || "genbank" in enabledDatabases || "biosample" in enabledDatabases

    script:
    def test_flag = params.prod_submission == false ? '--test' : ''
    def send_submission_email = params.send_submission_email == true ? '--send_email' : ''
    def dry_run = params.dry_run == true ? '--dry_run' : ''
    def biosample = "biosample" in enabledDatabases ? '--biosample' : ''
    def sra = "sra" in enabledDatabases ? '--sra' : ''
    def genbank = "genbank" in enabledDatabases ? '--genbank' : ''
    def wastewater = params.biosample_pkg == 'wastewater' ? '--wastewater' : ''
    def strip_pub = params.strip_pub_block == true ? '--strip_pub_block' : ''

    // Nextflow stages the per-file-type path lists (fastas/gffs/fq1s/fq2s/
    // nnps) into subdirectories in the work directory. Upstream workflows
    // emit each list in the same order as `samples`, dropping entries where
    // a sample lacks that file. To rebuild the per-sample argument list we
    // walk samples in order and pop the next entry from each file iterator
    // whenever the sample declares that key. Referencing the staged path
    // (rather than the original workDir URI stored in the samples map) is
    // what makes cloud executors work: the raw URI resolves to a
    // container-local /tostadas-work/<hash>/... path that doesn't exist.
    //
    // Nextflow binds `path` inputs to a Path object when it receives a
    // single file and to a List when it receives multiple. Calling
    // `.iterator()` on a Path iterates its NAME SEGMENTS (e.g., "fastas",
    // then the basename), so we must coerce to a list before iterating.
    // Empty lists (batches with no files of that type) stay as empty
    // lists and never get iterated because the sample map doesn't
    // declare that key.
    def asList = { v -> (v instanceof List) ? v : (v ? [v] : []) }
    def fasta_iter = asList(fastas).iterator()
    def gff_iter   = asList(gffs).iterator()
    def fq1_iter   = asList(fq1s).iterator()
    def fq2_iter   = asList(fq2s).iterator()
    def nnp_iter   = asList(nnps).iterator()

    def sample_args_list = samples.collect { sample ->
        def s = [
            "sample_id=${sample.meta.sample_id}",
            sample.get("fq1")       ? "fq1=${fq1_iter.next()}"     : null,
            sample.get("fq2")       ? "fq2=${fq2_iter.next()}"     : null,
            sample.get("nanopore")  ? "nnp=${nnp_iter.next()}"     : null,
            sample.get("fasta")     ? "fasta=${fasta_iter.next()}" : null,
            sample.get("gff")       ? "gff=${gff_iter.next()}"     : null
        ].findAll { it != null }
        .join(',')
        return "\"${s}\""
    }
    def sample_args = sample_args_list.collect { "--sample ${it}" }.join(' ')

    """
    submission_prep.py \
        --submission_name ${meta.batch_id} \
        --config_file $submission_config  \
        --metadata_file $batch_tsv \
        --identifier ${params.metadata_basename} \
        --species $params.organism_type \
        --mol_type '$params.mol_type' \
        --outdir  ${meta.batch_id} \
        ${sample_args} \
        --submission_mode $params.submission_mode \
        $test_flag \
        $send_submission_email \
        $sra $biosample $genbank \
        $wastewater \
        $dry_run \
        $strip_pub
    """
}