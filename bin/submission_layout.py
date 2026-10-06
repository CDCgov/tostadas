"""Locate submission XML files in prepared batch directories."""
import os


def sra_platforms(submission_folder):
    """Return the flat and platform-specific SRA destinations that contain XML."""
    base = os.path.join(submission_folder, 'sra')
    platforms = []
    if os.path.isfile(os.path.join(base, 'submission.xml')):
        platforms.append(None)
    for platform in ('illumina', 'nanopore'):
        if os.path.isfile(os.path.join(base, platform, 'submission.xml')):
            platforms.append(platform)
    return platforms


def discover_databases(submission_folder):
    """Discover databases with submission XML, including nested SRA batches."""
    databases = []
    if os.path.isfile(os.path.join(submission_folder, 'biosample', 'submission.xml')):
        databases.append('biosample')
    if sra_platforms(submission_folder):
        databases.append('sra')
    genbank = os.path.join(submission_folder, 'genbank')
    if os.path.isdir(genbank):
        if os.path.isfile(os.path.join(genbank, 'submission.xml')) or any(
            os.path.isfile(os.path.join(genbank, name, 'submission.xml'))
            for name in os.listdir(genbank)
            if os.path.isdir(os.path.join(genbank, name))
        ):
            databases.append('genbank')
    return databases
