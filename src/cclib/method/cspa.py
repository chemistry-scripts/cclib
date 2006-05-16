"""
cclib is a parser for computational chemistry log files.

See http://cclib.sf.net for more information.

Copyright (C) 2006 Noel O'Boyle and Adam Tenderholt

 This program is free software; you can redistribute and/or modify it
 under the terms of the GNU General Public License as published by the
 Free Software Foundation; either version 2, or (at your option) any later
 version.

 This program is distributed in the hope that it will be useful, but
 WITHOUT ANY WARRANTY, without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 General Public License for more details.

Contributions (monetary as well as code :-) are encouraged.
"""
import re,time
import Numeric
import random # For sometimes running the progress updater
from calculationmethod import Method

class CSPA(Method):
    """The C-squared population analysis"""
    def __init__(self,*args):

        # Call the __init__ method of the superclass
        super(CSPA, self).__init__(logname="Density",*args)
        
    def __str__(self):
        """Return a string representation of the object."""
        return "CSPA of" % (self.parser)

    def __repr__(self):
        """Return a representation of the object."""
        return 'CSPA("%s")' % (self.parser)
    
    def calculate(self,fupdate=0.05):
        """Perform a C-squared population analysis given the results of a parser"""
    
        if not self.parser.parsed:
            self.parser.parse()

        #do we have the needed info in the parser?
        if not hasattr(self.parser,"mocoeffs") \
          and not hasattr(self.parser,"nbasis"):
            self.logger.error("Missing mocoeffs or nbasis")
            return False #let the caller of function know we didn't finish

        self.logger.info("Creating attribute aoresults: array[3]")
        unrestricted=(len(self.parser.mocoeffs)==2)
        nmocoeffs=len(self.parser.mocoeffs[0])
        nbasis=self.parser.nbasis

        #determine number of steps, and whether process involves beta orbitals
        nstep=nmocoeffs
        if unrestricted:
            self.aoresults=Numeric.zeros([2,nmocoeffs,nbasis],"f")
            nstep+=nmocoeffs
        else:
            self.aoresults=Numeric.zeros([1,nmocoeffs,nbasis],"f")

        #intialize progress if available
        if self.progress:
            self.progress.initialize(nstep)

        step=0
        for spin in range(len(self.parser.mocoeffs)):

            for i in range(nmocoeffs):

                if self.progress and random.random()<fupdate:
                    self.progress.update(step,"C^2 Population Analysis")

                submocoeffs=self.parser.mocoeffs[spin][i]
                scale=Numeric.innerproduct(submocoeffs,submocoeffs)
                tempcoeffs=Numeric.multiply(submocoeffs,submocoeffs)
                self.aoresults[spin][i]=Numeric.divide(tempcoeffs,scale)

                step+=1

        if self.progress:
            self.progress.update(nstep,"Done")

#build list of groups of orbitals in each atom for atomresults
        if hasattr(self.parser,"aonames"):
            names=self.parser.aonames
        elif hasattr(self.parser,"foonames"):
            names=self.parser.fonames

        atoms=[]
        indices=[]

        name=names[0].split('_')[0]
        atoms.append(name)
        indices.append([0])

        for i in range(1,len(names)):
            name=names[i].split('_')[0]
            if name==atoms[-1]:
                indices[-1].append(i)
            else:
                atoms.append(name)
                indices.append([i])

        self.logger.info("Creating atomresults: array[3]")
        self.atomresults=self.partition(indices)

#create array for mulliken charges
        self.logger.info("Creating atomcharges: array[1]")
        size=len(self.atomresults[0][0])
        self.atomcharges=Numeric.zeros([size],"f")
        
        for spin in range(len(self.atomresults)):

            for i in range(self.parser.homos[spin]+1):

                temp=Numeric.reshape(self.atomresults[spin][i],(size,))
                self.atomcharges=Numeric.add(self.atomcharges,temp)
        
        if not unrestricted:
            self.atomcharges=Numeric.multiply(self.atomcharges,2)


        return True

    def partition(self,indices):

        if not hasattr(self,"aoresults"):
            self.calculate()

        natoms=len(indices)
        nmocoeffs=len(self.aoresults[0])
        
#build results Numeric array[3]
        if len(self.aoresults)==2:
            results=Numeric.zeros([2,nmocoeffs,natoms],"f")
        else:
            results=Numeric.zeros([1,nmocoeffs,natoms],"f")
        
#for each spin, splice Numeric array at ao index, and add to correct result row
        for spin in range(len(results)):

            for i in range(natoms): #number of groups

                for j in range(len(indices[i])): #for each group
                
                    temp=self.aoresults[spin,:,indices[i][j]]
                    results[spin,:,i]=Numeric.add(results[spin,:,i],temp)

        return results


if __name__=="__main__":
    import doctest,cspa
    doctest.testmod(cspa,verbose=False)