#!/usr/bin/env python3

class MainUtility:
    """ Class constructor for the main utility functions shared between annotation pipelines 
    """
    def __init__(self):
        """
        """
    
    @staticmethod
    def split_fasta(fasta_path, fasta_output):
        """
        Parses fasta file and writes it
        Possible bash command to make it work but cannot get rid of hanging new space, switching to less efficent but working solution
        os.system('cat multiFasta | awk '{ if (substr($0, 1, 1)==">"){filename=(substr($0,2) ".fasta")} print$0>>filename close(filename) }'')
        """
        # get the fasta lines that non empty
        with open(fasta_path, "r") as fasta_input:
            fasta_lines = [line.strip() for line in fasta_input.readlines() if line.strip()]
            fasta_input.close()
        # loop through list and write the lines
        for line in fasta_lines:
            if '>' in line:
                sample_name = line.split('>')[-1]
                fasta_sample_out = open(f"{fasta_output}{sample_name}.fasta", "w")
                fasta_sample_out.write(f">{sample_name}\n")
            else:
                fasta_sample_out.write(line)
                fasta_sample_out.close()
    
    @staticmethod
    def gff2tbl(samp_name, gff_loc, tbl_output):
        """ Converts the reformatted gff file to a table
        """
        # read in the reformatted gff file from above
        gff_input = open(f"{gff_loc}", "r")
        # specify the output tbl file path and open it up
        out_name = f"{tbl_output}{samp_name}.tbl"
        tbl = open(out_name, "w")

        # write fasta header for the sample name
        tbl.write('>' + 'Feature' + ' ' + samp_name + '\n')
        # iterate and skip the first two header rows
        for line in gff_input:
            line = line.split("\t")
            if not line[0].startswith('#'):
                # get the important features that we will write to tbl file
                feature = line[0]
                _type = line[2]
                start = line[3]
                stop = line[4]
                strand = line[6]
                if strand == '+':
                    tbl.write(start + '\t' + stop + '\t' + _type + '\n')
                else:
                    tbl.write(stop + '\t' + start + '\t' + _type + '\n')

                anns = line[8].split(';')
                check_unwanted_vals = [x for x in anns if x in ['\n', '\t', '/n', '/t']]
                if check_unwanted_vals:
                    [anns.remove(x) for x in check_unwanted_vals]
                # check if unwanted characters in there
                for x in range(len(anns)):
                    anns[x] = anns[x].replace('%3B', ';')
                    anns[x] = anns[x].replace('%2C', ',')
                    try:
                        assert '%3B' not in anns[x] and '%2C' not in anns[x]
                    except AssertionError:
                        raise AssertionError(f"Could not replace %3B or %2C from line")

                for item in anns[0:-2]:
                    item = item.split('=')
                    tbl.write('\t' + '\t' + '\t' + item[0] + '\t' + item[1] + '\n')
                    
                item = anns[-1].split('=')
                tbl.write('\t' + '\t' + '\t' + item[0] + '\t' + item[1])

            if not line:
                break


class GFFChecksUtility:
    def __init__(self):
        """
        """
    
    @staticmethod
    def check_note(field_value_mapping):
        # now check whether a # sign is in the note section
        if 'note' in list(field_value_mapping.keys()) and '#' in field_value_mapping['note']:
            field_value_mapping['note'] = field_value_mapping['note'].replace('#', '')
            try:
                assert '#' not in field_value_mapping['note']
            except AssertionError:
                raise AssertionError(
                    f"Found a # sign in the note field that could not be removed: {field_value_mapping['note']}")
        return field_value_mapping
    
