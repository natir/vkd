version 1.2

struct VcfCompareOutput {
  File summary
  File truth
  File query
}

struct VcfWithIndex {
  File vcf
  File tbi
}

struct FastaWithIndex {
  File fasta
  File fai
}
