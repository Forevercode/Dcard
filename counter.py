
class Counter:
    def __init__(self,start=0,end="infinite",step=1):
        if type(start)!=int or type(step)!=int:
            raise TypeError('Both Arguments "start" and "step" expect int object')

        if type(end)!=int and end!="infinite":
            raise TypeError('Arguments "end"  only accept int object or string"infinite" passed"')

        self.start=start
        self.end = end
        self.step=step

        self.current=self.start

    def __iter__(self):
        return self

    def __next__(self):
        if self.end=="infinite":
           return self.__iterinfinite()
        else :
           return self.__iterfinite()

    def __iterinfinite(self):
        current = self.current
        self.current += self.step
        return current

    def __iterfinite(self):
        if self.current>=self.end:
            raise StopIteration

        current=self.current
        self.current+=self.step
        return current

    def last_value(self):
        return self.current-self.step




