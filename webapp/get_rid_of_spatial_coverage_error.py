import os

def get_rid_of_spatial_coverage_error():
    
    infile = '/code/opendrift/models/basemodel.py'
    outfile = '/code/opendrift/models/basemodel.fixed.py'
    
    with open(infile, 'r') as inp, open(outfile, 'w') as out:
        # Read original variables.py file
        lines = iter(inp.readlines())
        
        for line in lines:
            if 'except NotCoveredError' in line:
                out.write(line)
                out.write('                    logger.debug(e)\n')
                next(lines)                
            else:
                out.write(line)
            
    os.remove(infile); os.rename(outfile, infile)
            
if __name__ == '__main__':
    get_rid_of_spatial_coverage_error()