import groovy.json.JsonGenerator
import groovy.json.JsonGenerator.Converter

nextflow.enable.dsl=2

// comes from nf-test to store json files
params.nf_test_output  = ""

// include dependencies


// include test process
include { LIFTOFF_CLI } from '/scicomp/home-pure/rjd0/tostadas/modules/local/liftoff_cli_annotation/main.nf'

// define custom rules for JSON that will be generated.
def jsonOutput =
    new JsonGenerator.Options()
        .addConverter(Path) { value -> value.toAbsolutePath().toString() } // Custom converter for Path. Only filename
        .build()

def jsonWorkflowOutput = new JsonGenerator.Options().excludeNulls().build()


workflow {

    // run dependencies
    

    // process mapping
    def input = []
    
                input[0] = [ [ batch_id: "batch_1",  batch_tsv: file("/scicomp/home-pure/rjd0/tostadas/tests/modules/local/prep_submission/batch_1.tsv"), sample_id: "NY0006" ],
                            file("/scicomp/home-pure/rjd0/tostadas/assets/sample_fastas/mpox/NY0006.fasta")]
                input[1] = file("/scicomp/home-pure/rjd0/tostadas/assets/ref/ref.MPXV.NC063383.v7.fasta")
                input[2] = file("/scicomp/home-pure/rjd0/tostadas/assets/ref/ref.MPXV.NC063383.v7.gff")
                
    //----

    //run process
    LIFTOFF_CLI(*input)

    if (LIFTOFF_CLI.output){

        // consumes all named output channels and stores items in a json file
        for (def name in LIFTOFF_CLI.out.getNames()) {
            serializeChannel(name, LIFTOFF_CLI.out.getProperty(name), jsonOutput)
        }	  
      
        // consumes all unnamed output channels and stores items in a json file
        def array = LIFTOFF_CLI.out as Object[]
        for (def i = 0; i < array.length ; i++) {
            serializeChannel(i, array[i], jsonOutput)
        }    	

    }
  
}

def serializeChannel(name, channel, jsonOutput) {
    def _name = name
    def list = [ ]
    channel.subscribe(
        onNext: {
            list.add(it)
        },
        onComplete: {
              def map = new HashMap()
              map[_name] = list
              def filename = "${params.nf_test_output}/output_${_name}.json"
              new File(filename).text = jsonOutput.toJson(map)		  		
        } 
    )
}


workflow.onComplete {

    def result = [
        success: workflow.success,
        exitStatus: workflow.exitStatus,
        errorMessage: workflow.errorMessage,
        errorReport: workflow.errorReport
    ]
    new File("${params.nf_test_output}/workflow.json").text = jsonWorkflowOutput.toJson(result)
    
}
