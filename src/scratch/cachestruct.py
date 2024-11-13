class cache:

    """
    Class to instantiate a cache data structure for use in simulator.

    Supports different sizes of cache and associativity. Data structure
    is a nested dictionary in which the first level is the set with keyed
    by the set index (0 to n-1), second level contains key pair for the
    PLRU bits for that index and n ways keyed 0 to n-1, the thrid level
    contains key pairs for the valid, dirty, mesi, and tag bits.

    Attributes: 
        numSets: total number of sets in the cache
        assoc: associativity of the cache (number of lines per set)
    """

    def __init__(self, numSets, assoc):

        self.numSets = numSets
        self.assoc = assoc

        """
        contruct data structure using dictionary comprehension
        """
        self.set = {index: {way: {'valid':0, 'dirty':0, 'mesi':0, 'tag':0} for way in range(assoc)} for index in range(numSets)}

        """
        Because the data structure is initially built using dictionary 
        comphrension, which cannot be used in combination with other
        dictionary entries, add plru key separately.
        """
        for i in range(numSets): 
            self.set[i]['plru'] = 0