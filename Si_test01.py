from workload_parser import WorkloadParser

# Initialize with default config
parser = WorkloadParser()



# Parse entire directory
results = parser.parse_directory(r"\\10.54.63.126\Pnpext\Siwoo\data\WW2532.2_CataV3ff_test")


print(results)