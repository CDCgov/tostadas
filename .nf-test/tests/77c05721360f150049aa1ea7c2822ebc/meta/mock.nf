import groovy.json.JsonGenerator
import groovy.json.JsonGenerator.Converter

nextflow.enable.dsl=2

// comes from nf-test to store json files
params.nf_test_output  = ""

// include dependencies


// include test workflow
include { RUN_BAKTA } from '/scicomp/home-pure/rjd0/tostadas/subworkflows/local/bakta.nf'

// define custom rules for JSON that will be generated.
def jsonOutput =
    new JsonGenerator.Options()
        .addConverter(Path) { value -> value.toAbsolutePath().toString() } // Custom converter for Path. Only filename
        .build()

def jsonWorkflowOutput = new JsonGenerator.Options().excludeNulls().build()

workflow {

    // run dependencies
    

    // workflow mapping
    def input = []
    
                input[0] = Channel.of([
                    [ batch_id: "batch_1", batch_tsv: file("/scicomp/home-pure/rjd0/tostadas/tests/subworkflows/local/batch_1_bacteria.tsv"), sample_id: "CP040557" ],
                    file("/scicomp/home-pure/rjd0/tostadas/assets/sample_fastas/bacteria/CP040557.fasta")
                ])
                
    //----

    //run workflow
    RUN_BAKTA(*input)
    
    if (RUN_BAKTA.output){

        // consumes all named output channels and stores items in a json file
        for (def name in RUN_BAKTA.out.getNames()) {
            serializeChannel(name, RUN_BAKTA.out.getProperty(name), jsonOutput)
        }	  
    
        // consumes all unnamed output channels and stores items in a json file
        def array = RUN_BAKTA.out as Object[]
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
