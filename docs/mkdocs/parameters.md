# Parameters

Default parameters are given in the nextflow.config file. This table lists the parameters that can be changed to a value, path or true/false. When changing these parameters pay attention to the required inputs and make sure that paths line-up and values are within range. To change a parameter you may change with a flag after the nextflow command or change them within your nextflow.config file.

*   Please note the correct formatting and the default calculation of submission\_wait\_time at the bottom of the params table.

## Input Files

| Param | Description | Input Required |
| --- | --- | --- |
| \--ref\_fasta\_path | Reference Sequence file path | Yes (path as string) |
| \--meta\_path | Meta-data file path for samples | Yes (path as string) |
| \--ref\_gff\_path | Reference gff file path for annotation | Yes (path as string) |

## General Subworkflow

| Param | Description | Input Required |
| --- | --- | --- |
| \--submission | Toggle for running submission | Yes (true/false as bool) |
| \--annotation | Toggle for running annotation | Yes (true/false as bool) |
| \--cleanup | Toggle for running cleanup subworkflows | Yes (true/false as bool) |
| \--fetch\_reports\_only | Toggle for only fetching submission reports | Yes (true/false as bool) |

## General Settings

| Param | Description | Input Required |
| --- | --- | --- |
| \--date\_format\_flag | Flag to specify the date format. Options: s (default, YYYY-MM), v (verbose, YYYY-MM-DD), o (original, unchanged) | Yes (string) |
| \--publish\_dir\_mode | Mode for publishing directory, e.g., 'copy' or 'move' | Yes (string) |
| \--remove\_demographic\_info | Flag to remove demographic info. If true, values in host\_sex, host\_age, race, ethnicity are set to 'Not Provided' | Yes (true/false) |

## Cleanup Subworkflow

| Param | Description | Input Required |
| --- | --- | --- |
| \--clear\_nextflow\_log | Clears nextflow work log | Yes (true/false as bool) |
| \--clear\_work\_dir | Param to clear work directory created during workflow | Yes (true/false as bool) |
| \--clear\_conda\_env | Clears conda environment | Yes (true/false as bool) |
| \--clear\_nf\_results | Remove results from nextflow outputs | Yes (true/false as bool) |

## General Output

| Param | Description | Input Required |
| --- | --- | --- |
| \--output\_dir | File path to submit outputs from pipeline | Yes (path as string) |
| \--overwrite\_output | Toggle to overwriting output files in directory | Yes (true/false as bool) |

## Validation

| Param | Description | Input Required |
| --- | --- | --- |
| \--val\_output\_dir | File path for outputs specific to validate sub-workflow | Yes (folder name as string) |
| \--validate\_custom\_fields | Toggle checks/transformations for custom metadata fields on/off | No (true/false as bool) |
| \--custom\_fields\_file | Path to the JSON file containing custom metadata fields and their information | No (path as string) |
| \--validate\_params | Flag to enable or disable parameter validation | No (true/false as bool) |

## Liftoff

| Param | Description | Input Required |
| --- | --- | --- |
| \--final\_liftoff\_output\_dir | File path to liftoff specific sub-workflow outputs | Yes (folder name as string) |
| \--lift\_print\_version\_exit | Print version and exit the program | Yes (true/false) |
| \--lift\_print\_help\_exit | Print help and exit the program | Yes (true/false) |
| \--lift\_parallel\_processes | Number of parallel processes to use for liftoff | Yes (integer) |
| \--lift\_child\_feature\_align\_threshold | Map only if its child features align with sequence identity greater than this value | Yes (float) |
| \--lift\_unmapped\_feature\_file\_name | Name of unmapped features file | Yes (path as string) |
| \--lift\_copy\_threshold | Minimum sequence identity in exons/CDS for which a gene is considered a copy; default is 1.0 | Yes (float) |
| \--lift\_distance\_scaling\_factor | Distance scaling factor; default is 2.0 | Yes (float) |
| \--lift\_flank | Amount of flanking sequence to align as a fraction of gene length | Yes (float between 0.0 and 1.0) |
| \--lift\_overlap | Maximum fraction of overlap allowed by two features | Yes (float between 0.0 and 1.0) |
| \--lift\_mismatch | Mismatch penalty in exons when finding best mapping; default is 2 | Yes (integer) |
| \--lift\_gap\_open | Gap open penalty in exons when finding best mapping; default is 2 | Yes (integer) |
| \--lift\_gap\_extend | Gap extend penalty in exons when finding best mapping; default is 1 | Yes (integer) |
| \--lift\_minimap\_path | Path to minimap if you did not use conda or pip | Yes (N/A or path as string) |
| \--lift\_features\_database\_name | Name of the feature database, if none, will use ref gff path to construct one | Yes (N/A or name as string) |
| \--lift\_feature\_types | Path to the file containing feature types | Yes (path as string) |
| \--lift\_coverage\_threshold | Minimum coverage threshold for feature mapping | Yes (float) |
| \--repeatmasker\_liftoff | Flag to enable or disable RepeatMasker and Liftoff steps | Yes (true/false) |

## VADR

| Param | Description | Input Required |
| --- | --- | --- |
| \--vadr | Toggle for running VADR annotation | Yes (true/false as bool) |
| \--vadr\_output\_dir | File path to vadr specific sub-workflow outputs | Yes (folder name as string) |
| \--vadr\_models\_dir | File path to models for MPXV used by VADR annotation | Yes (folder name as string) |

## BAKTA

Controlling Bakta within TOSTADAS uses parameters of the same name with prefix `--bakta_` as described below. For more details, visit the [Bakta GitHub page](https://github.com/oschwengers/bakta).

| Param | Description | Input Required |
| --- | --- | --- |
| \--bakta\_db\_path | Path to Bakta database if user is supplying database | No (path to database) |
| \--download\_bakta\_db | Option to download Bakta database | Yes (true/false) |
| \--bakta\_db\_type | Bakta database type (light or full) | Yes (string) |
| \--bakta\_output\_dir | File path to bakta specific sub-workflow outputs | Yes (folder name as string) |
| \--bakta\_min\_contig\_length | Minimum contig size | Yes (integer) |
| \--bakta\_threads | Number of threads to use while running annotation | Yes (integer) |
| \--bakta\_genus | Organism genus name | Yes (N/A or name as string) |
| \--bakta\_species | Organism species name | Yes (N/A or name as string) |
| \--bakta\_strain | Organism strain name | Yes (N/A or name as string) |
| \--bakta\_plasmid | Name of plasmid | Yes (unnamed or name as string) |
| \--bakta\_locus | Locus prefix | Yes (contig or name as string) |
| \--bakta\_locus\_tag | Locus tag prefix | Yes (autogenerated or name as string) |
| \--bakta\_translation\_table | Translation table | Yes (integer) |
| \--bakta\_gram | Gram type for signal peptide predictions | No ('+' '-' '?') |
| \--bakta | Toggle for running Bakta annotation | Yes (true/false as bool) |
| \--bakta\_complete | Complete Bakta annotation | Yes (string) |
| \--bakta\_compliant | Compliant with Bakta standards | Yes (true/false) |
| \--bakta\_keep\_contig\_headers | Keep contig headers | Yes (string) |
| \--bakta\_proteins | Proteins to include in annotation | Yes (string) |
| \--bakta\_replicons | Replicons to include in annotation | Yes (string) |
| \--bakta\_skip\_cds | Skip CDS annotation | Yes (string) |
| \--bakta\_skip\_crispr | Skip CRISPR annotation | Yes (string) |
| \--bakta\_skip\_gap | Skip gap annotation | Yes (string) |
| \--bakta\_skip\_ncrna | Skip ncRNA annotation | Yes (string) |
| \--bakta\_skip\_ncrna\_region | Skip ncRNA region annotation | Yes (string) |
| \--bakta\_skip\_ori | Skip origin annotation | Yes (string) |
| \--bakta\_skip\_plot | Skip plot generation | Yes (true/false) |
| \--bakta\_skip\_pseudo | Skip pseudogene annotation | Yes (string) |
| \--bakta\_skip\_rrna | Skip rRNA annotation | Yes (string) |
| \--bakta\_skip\_sorf | Skip sORF annotation | Yes (string) |
| \--bakta\_skip\_tmrna | Skip tmRNA annotation | Yes (string) |
| \--bakta\_skip\_trna | Skip tRNA annotation | Yes (string) |

## Sample Submission

| Param | Description | Input Required |
| --- | --- | --- |
| \--genbank | Submit to GenBank | Yes (true/false as bool) |
| \--sra | Submit to SRA | Yes (true/false as bool) |
| \--biosample | Submit to Biosample | Yes (true/false as bool) |
| \--gisaid | Submit to GISAID | Yes (true/false as bool) |
| \--submission\_output\_dir | Either name or relative/absolute path for the outputs from submission | Yes (name or path as string) |
| \--submission\_prod\_or\_test | Whether to submit samples for test or actual production | Yes (prod or test as string) |
| \--submission\_config | Configuration file for submission to public repos | Yes (path as string) |
| \--submission\_wait\_time | Calculated based on sample number (3 \* 60 secs \* sample\_num) | integer (seconds) |
| \--send\_submission\_email | Toggle email notification on/off | Yes (true/false as bool) |
| \--submission\_mode | Mode of submission | Yes (string) |
| \--update\_submission | Flag to enable or disable updating existing submissions | Yes (true/false as bool) |

❗ Important note about send\_submission\_email: An email is only triggered if Genbank is being submitted to AND `table2asn` is the `genbank_submission_type`. As for the recipient, this must be specified within your submission config file under 'general' as 'notif\_email\_recipient'\*
