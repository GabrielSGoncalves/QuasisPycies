#!/usr/bin/python
# Author: Gabriel dos Santos Goncalves
# Rio de Janeiro, Brasil - march 2016

'''

       =======  QuasiPycies =======

Python 3 module to calculate diversity indices from NGS data. It consists of two main classes (Clusters and Pileup) and extra functions for convertion and parsing different file formats.

class Clusters 
    It uses a fasta file as input. The fasta file must have number of reads ("size=") on each sequence name and the respective percentage. It can be generated by using clustering tools like Usearch or BBmap that write the number of reads for each cluster.

    eg:

    >ReadA;size=180_90.0%
    AAATTTCCCGGG
    >ReadB;size=20_10.0%
    TTTAAATTTGGG 

    Functions:  shannon_entropy
                simpsons_index
                simpsons_index_of_diversity
                simpsons_Reciprocal_Index
                clusters_object_to_fasta
                filtering_clusters_by_percentage
                number_haplotypes
                filtering_Clusters

class Pileup
    It uses a mpileup file as input. The mpileup file can be generated from a SAM/BAM file using samtools (more information in README file). The information of stacked bases for each position in the alignment is used to calculated intrapopulation heterogeneity. 
        
    Functions:  nucleotide_diversity
                polymorphic_sites


Extra functions
                filtering_clusters_by_percentage
                sam_to_fasta
                fastq_to_fasta
                multiline_fasta_to_singleline
                clusters_to_single_reads
'''

import re 
import math

class Clusters(object):

    def __init__(self, fasta):
        '''This initial function parses the fasta file and defines the instances of the class. 

        - self.dict_fasta: This dictionary has as key the name of the sequence
        a as value a list with sequence, percentage and number of reads.
        - self.names: list with all the names of the sequence clusters
        - self.sequences: list with all the sequences
        - self.percentages: list with all the percentages
        - self.number_reads: list with all the numer of reads for each clusters
        '''
        
        #Load the file and read lines
        self.fasta_file = open(fasta, "r").readlines()

        # Define the instances
        self.dict_fasta = {}
        self.names = []
        self.sequences = []
        self.percentages = []
        self.number_reads = []

        # Iterate over the lines of the file
        for number, line in enumerate(self.fasta_file):
            if line.startswith(">"):
                
                # Search for the number of reads in sequence name 
                n_search = re.search(";size=(\d+)", line)
                n = int(n_search.group(1))
                # Store the number of reads in a list
                self.number_reads.append(n)
                
                # Search for the percentage in sequence name
                percentage_search = re.search("(\d+.\d+)%", line)
                percentage = float(percentage_search.group(1))
                # Store the percentage in a list
                self.percentages.append(percentage)
                    
                # Define the name of the sequence without ">", number of reads 
                # and percentage
                name = line[1:n_search.start()]
                # Store the name in a list
                self.names.append(name)
                
                # Store the sequence in a list
                sequence = self.fasta_file[number+1]
                self.sequences.append(sequence)
                
                self.dict_fasta [name] = [sequence, percentage, n]
                
      
    
    def shannon_entropy(self, minimun_perc):
        ''' Shannon Entropy is a diversity index that measures the evenness of the population. It uses the values of size of haplotypes (subpopulations) in the sample. Must specify the minimun_perc (from 0 to 1) of clusters to consider for the calculation of the index (usually a value based on the error rate of the PCR/sequencing). 
        '''
        number_reads = 0
        list_sizes = []

        for key, value in self.dict_fasta.items():
            
            if value[1] >=  minimun_perc:
                list_sizes.append(value[2])
                number_reads += value[2]
        entropy = 0

        for v in list_sizes:
            subpop = (v/number_reads) * math.log(v/number_reads)
            entropy += subpop

        S = -(entropy/math.log(number_reads))
        return(round(S,3))

   
    def simpsons_index(self):
        ''' Simpson's index measures the probability that two individuals (in this case reads) randomly selected from a sample will belong to the same species (in this case cluster).
        '''
        
        D = 0
        for element in self.number_reads:
            d= (element/sum(self.number_reads))**2
            D += d
            
        return(round(D,2))

    
    def simpsons_index_of_diversity(self):
        ''' Simpson's index of diversity measures the probability that two individuals (in this case reads) randomly selected from a sample will belong to different species (in this case cluster). 

        Simpson's index of diversity = 1 - Simpson's index
        '''

        D = 0
        for element in self.number_reads:
            d= (element/sum(self.number_reads))**2
            D += d
            
        return(round(1-D, 2))

    
    def simpsons_reciprocal_index(self):
        '''Simpson's Reciprocal Index starts with 1 as the lowest value, representing a sample/community with just one sample. The greater the value, greater the diversity, meaning the total number of species. 

        Simpson's Reciprocal Index = 1 / Simpson's index
        '''
        
        D = 0
        for element in self.number_reads:
            d= (element/sum(self.number_reads))**2
            D += d
            
        return(round(1/D,2))


    def clusters_object_to_fasta(self, fasta_name):
        ''' This function creates a fasta file from the dict_fasta object. Must provide a fasta_name as output file.
        '''
        
        # First we create a file to receive the data
        fasta_output = open(fasta_name, "w")
        
        # Then we iterate through the self.dict_fasta dictionary 
        for key, value in self.dict_fasta.items():
            fasta_output.write(">" + key + "_size=" + str(value[1]) + "_" + str(value[1]) + "%" + "\n")
            fasta_output.write(value[0])

    
    def filtering_clusters_by_percentage_to_fasta(self, minimun_perc, output_fasta):
        ''' This function filters the clusters by percentage and writes it to an output file. A minimun_perc (from 0 to 1) must be provided to filter only the reads above this value and also the file name (output_fasta).
        '''
        file_out = open (output_fasta, "w")
        number_reads = 0
        list_sizes = []

        for key, value in self.dict_fasta.items():
            n = int(value[2])
            number_reads += n
        
        print(number_reads)

        for key, value in self.dict_fasta.items():
            if value[2] >= (number_reads * float(minimun_perc)):
                print((number_reads * float(minimun_perc)))
                print(value[2])
                file_out.write(value[0])
                

    def number_haplotypes(self, value_type, cutoff):
        ''' This function counts the number of haplotypes greater than a cutoff. The cutoff can be specified "percentage" or "number_reads" (must discribe in value_type parameter). 
        '''
        # Define the two variables to hold the number of haplotypes
        counter_haplotypes = 0
        counter_haplotypes_over_min_number = 0

        # If "percentage" is used to filter the haplotypes, choose a number from 0 to 100
        if value_type == "percentage":
            for key in self.dict_fasta.keys():
                counter_haplotypes += 1
                if self.dict_fasta [key][1] >= cutoff:
                    counter_haplotypes_over_min_number +=1
                    
        # If "number_reads" used to filter the haplotypes, choose a number an absolute minimun number
        elif value_type == "number_reads":
            for key in self.dict_fasta.keys():
                counter_haplotypes += 1
                if self.dict_fasta [key][2] >= cutoff:
                    counter_haplotypes_over_min_number +=1
                   
                   
        print ("From a total of " + str(counter_haplotypes) + " haplotypes only " + str(counter_haplotypes_over_min_number) + " are above the cutoff")
        return (counter_haplotypes_over_min_number)
   


class Pileup(object):     
    
    def __init__(self, pileup_file, min_reads_per_position=0):
        '''    This initial function is in charge of dealing with pileup files, parsing it and calculating diversity indices like nucleotide diversity and number of polymorphic sites. Must provide the name of mpileup file and minimun number of reads per position to be considered.
        '''   
        # Create the dictionary to store each base data
        self.dict_pileup = {}
        self.polymorphic_sites_dict = {}

        #Load the file and read lines
        self.pileup_file = open(pileup_file, "r").readlines()
        
        # Iterate over the lines of the pileup file storing the information 
        # of each base position  
        for n,line in enumerate(self.pileup_file):
            line_elements =  line.split("\t")
            ref= line_elements[0]
            line_number = line_elements[1]
            ref_base = line_elements[2]
            pos_depth= line_elements[3]
            base_qualities= line_elements[5]
            pos_bases_original = line_elements[4]
            if n < min_reads_per_position:
                pos_bases_sub_1 = re.sub(r"\^.([ACTGNacgtn.,])", r"\1", pos_bases_original).upper()    
                pos_bases_sub_2 = re.sub("[.,]",ref_base, pos_bases_sub_1).upper()
                self.dict_pileup[line_number]= pos_bases_sub_2
            else:
                pos_bases_sub = re.sub("[.,]",ref_base, pos_bases_original).upper()
                self.dict_pileup[line_number]= pos_bases_sub

    
    def nucleotide_diversity(self):
        ''' Nucleotide diversity measures the intrapopulation diversity. It considers each nucleotide, of each position in the genome of the individuals in the population.
        '''

        nuc_diversity_list=[]

        for pos in self.dict_pileup.values():
            A = pos.upper().count("A")
            T = pos.upper().count("T")
            C = pos.upper().count("C")
            G = pos.upper().count("G")
            reads = A + C + T + G
            Di = (float((A*C)+(A*G)+(A*T)+(C*G)+(C*T)+(G*T)))/(float((reads**2 - reads)/2))
            nuc_diversity_list.append(Di)

        total_nuc_diversity = sum(nuc_diversity_list)/len(self.dict_pileup.values())
        
        return(round(total_nuc_diversity,4))


    def polymorphic_sites(self, value_type, cutoff):
        ''' The polymorphic_sites function measures the number of position in the genome that have multiple alleles (bases). It consider only bases above the cutoff value. Value_type can be "percentage" (from 0 to 100) or "number_reads" (absolute value).
        '''
        number_polymorphic_sites = 0

        # For value_type equal to "percentage"
        if value_type == "percentage":

            # Loop through the self.dict_pileup items
            for key, value in self.dict_pileup.items():
                A = value.upper().count("A")
                T = value.upper().count("T")
                C = value.upper().count("C")
                G = value.upper().count("G")

                list_n_bases = [A,T,C,G]
                list_n_bases.sort()
                    
                if list_n_bases[2] > sum(list_n_bases) * cutoff:
                    number_polymorphic_sites += 1
                    self.polymorphic_sites_dict[key] = value

        # For value_type equal to "number_reads"
        elif value_type == "number_reads":
            
            # Loop through the self.dict_pileup items
            for key, value in self.dict_pileup.items():
            	A = value.upper().count("A")
                T = value.upper().count("T")
                C = value.upper().count("C")
                G = value.upper().count("G")

                list_n_bases = [A,T,C,G]
                list_n_bases.sort()

                if list_n_bases[2] > cutoff:
                    number_polymorphic_sites += 1
                    self.polymorphic_sites_dict[key] = value


        return(number_polymorphic_sites)


# These are python functions that may be used on the main workflow

def filtering_fastaclusters_by_percentage(input1, minimun_perc, output1):
    '''This function filters a clustered fasta file and writes it down to another fasta file. Must provide input fasta file name, minimun percentage (from 0 to 1) as cutoff and output file name.
    '''
    # Open input fasta and create output fasta
    file_in = open (input1, "r")
    fasta_in = file_in.readlines()
    file_out = open (output1, "w")
    number_reads = 0
    list_sizes = []

    # To calculate the total number of reads
    for number, line in enumerate(fasta_in):
        if line[0]==">":
            n_search = re.search(";size=(\d+)", line)
            n = int(n_search.group(1))
            number_reads += n
    
    # Loop through the sequences
    for number, line in enumerate(fasta_in):
        if line[0]==">":
            n_search = re.search(";size=(\d+)", line)
            n = int(n_search.group(1))
            # Check if the cluster is above the minimun_perc
            if n >= (number_reads * float(minimun_perc)):
                file_out.write(line.rstrip() + '_' + str(round(float((n/number_reads)*100),2)) + "%" + "\n")
                file_out.write(fasta_in[number+1])

    

def normalize_percentage(input1,output1):
    '''This function normalizes sequence clusters after filtering. As part of the clusters are below the error rate, after filtering the remaining clusters percentages would not sum to 100%. So this function recalculates the percentage based on the number of reads of clusters above the error rate and writes it to the sequence name.
    '''
    file_in = open (input1, "r")
    fasta_in = file_in.readlines()
    file_out = open (output1, "w")
    number_reads = 0
    list_sizes = []

    for number, line in enumerate(fasta_in):
        if line[0]==">":
            n_search = re.search(";size=(\d+)", line)
            n = int(n_search.group(1))
            number_reads += n
    
    for number, line in enumerate(fasta_in):
        if line[0]==">":
            n_search = re.search(";size=(\d+)", line)
            n = int(n_search.group(1))
            new_n = round(float(100 *(n/number_reads)),2)
            new_line = re.sub("(\d+.\d+)%",str(new_n), line)
            file_out.write(new_line.rstrip() + "%" + "\n")
            file_out.write(fasta_in[number+1])



def sam_to_fasta(SAM_file, fasta_file):
    '''Converts sam file to fasta file. Must provide the name of the sam file and fasta file as paramenters.
    '''
    SAM = open (SAM_file, "r")
    SAM_lines = SAM.readlines()
    fasta_file = open (fasta_file, "w")

    for line in SAM_lines:
        if line[0] != "@":
            line_elements = line.split("\t")
            fasta_file.write(">" + str(line_elements[0] + "\n"))
            fasta_file.write(line_elements[9]+ "\n")


def fastq_to_fasta(fastq_file, fasta_file):
    '''This function converts fastq files into fasta files. Must provide the name of the fastq file and fasta file as paramenters.
    '''
    
    # Open input fastq file and create output fasta file 
    fastq1 = open (fastq_file, "r")
    fastq = fastq1.readlines()
    fasta = open (fasta_file, "w")
    
    # Create lists with the number of the lines carrying the name of reads and
    # bases 
    list_name_lines = [] # 0
    list_bases_lines = [] # 1
     
    for a in range(0,(len(fastq)+1),4):
        list_name_lines.append(a)
    
    for b in range(1,(len(fastq)+1),4):
        list_bases_lines.append(b)
    
    # Iterate through each line in the file and copy only the ones that 
    # represent the name and the bases of each read to the new fasta file. 
    # Also replacing the "@" for the ">" before each read name.     
    for number, line in enumerate(fastq):
        if number in list_name_lines:
            mod1 = re.sub('^@','>', line)
            fasta.write(mod1)
            
        elif number in list_bases_lines:
            fasta.write(line)
    

def multiline_fasta_to_singleline(input1, output1):
    '''Converts multiline fasta to single line fasta format. Must provide name of original (multiline fasta) fasta and output fasta (single line fasta).
    '''
    fasta = open (input1, "r")
    fasta_ML = fasta.readlines()
    fasta_SL = open (output1, "w")

    for n,line in enumerate(fasta_ML):
        if line.startswith(">"):
            fasta_ML[n] =  "\n" + line.rstrip() 
        else:
            fasta_ML[n]=line.rstrip()

    data = ('|'.join(fasta_ML))

    data = data[1:]
    
    x = re.sub(";\|","\n",data)
    y = re.sub("\|","",x)
    fasta_SL.write(y+"\n")


def clusters_to_single_reads(input1, output1):
    '''Converts clusters back to single reads. Must provide name of clusters file and the single reads fasta file.
    '''
    fasta = open (input1, "r")
    fasta_ML = fasta.readlines()
    fasta = open (output1, "w")

    for n,line in enumerate(fasta_ML):
        if line.startswith(">"):
            count_match = re.search("size=(\d+)", line)
            count_number = int(count_match.group(1))
            read_name = line[:line.find(";size")]
            
            for i in range(0,count_number):
                fasta.write(read_name + "_" + str(i)+"\n")
                fasta.write(fasta_ML[n+1])


def writing_percentage_to_clusters(input1, minimun_perc, output1):
    '''This function filters a clustered fasta file and writes it down to another fasta file. Must provide input fasta file name, minimun percentage (from 0 to 1) as cutoff and output file name.
    '''
    file_in = open (input1, "r")
    fasta_in = file_in.readlines()
    file_out = open (output1, "w")
    number_reads = 0
    list_sizes = []

    for number, line in enumerate(fasta_in):
        if line[0]==">":
            n_search = re.search(";size=(\d+)", line)
            n = int(n_search.group(1))
            number_reads += n


    for number, line in enumerate(fasta_in):
        if line[0]==">":
            n_search = re.search(";size=(\d+)", line)
            n = int(n_search.group(1))
            if n >= (number_reads * float(minimun_perc)):
                file_out.write(line.rstrip() + str(round(float((n/number_reads)*100),2)) + "%" + "\n")
                file_out.write(fasta_in[number+1])