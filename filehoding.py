import os
class FileHolding:
    def having_file_exist(*argv):
        for path in argv:
            if not os.path.exists(path) :
                with open(path,"w") as file:
                    pass

