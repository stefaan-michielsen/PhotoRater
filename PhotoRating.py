import os
import Glicko

class PhotoRatingDb:
    def __init__(self, curdir):
        self.curdir = curdir
        self.ratingFilePath = self.curdir / "photoRaterDB.txt"
        self.loadRatings()
        self.rereadFilelist(self.curdir)

    def loadRatings(self):
        self.photos = {}
        if os.path.exists(self.ratingFilePath):
            f = open(self.ratingFilePath, 'r')
            for line in f.readlines():
                 info = line.split(":")
                 self.photos[info[0]] = PhotoRating(info[0], info[1])
            f.close()

    def GoodPhotosForGrouping(self):
        result = []
        for photoid,rating in self.photos.items():
            if (rating.Status  == StatusEnum.GOOD) and (rating.Grouped ==
                    GroupedEnum.UNCHECKED):
                result.append(photoid)
        return result

    def GroupHasBestPhoto(self, group):
        photo_rating = [];
        for photoid in group:
            photo_rating.append(self.photos[photoid].GroupMu)
        zero_values = 0
        start_values = 0
        id_values = 0
        for i in photo_rating:
            if i == 0:
                zero_values += 1
            if i == 1:
                start_values += 1
            if i > 1:
                id_values += 1
        if (id_values == 1 and start_values == 0):
            return True
        return False

    def BestPhotoOfGroup(self, group):
        for photoid in group:
            if self.photos[photoid].GroupMu > 1:
                return photoid

    def GroupedPhotosPackets(self):
        result = {}
        first = True
        currentGroup = []
        currentGroupId = ""
        for photoid,rating in self.photos.items():
            if (rating.Grouped == GroupedEnum.GROUPED):
                if rating.GroupId == currentGroupId:
                    currentGroup.append(photoid)
                else:
                    if first:
                        first = False
                    else:
                        if not self.GroupHasBestPhoto(currentGroup):
                            result[currentGroupId] = currentGroup
                        else:
                            bestphoto = self.BestPhotoOfGroup(currentGroup)
                            for groupphoto in currentGroup:
                                 self.photos[groupphoto].GroupId = bestphoto
                    currentGroupId = rating.GroupId
                    currentGroup = [photoid]

        if not self.GroupHasBestPhoto(currentGroup):
              result[currentGroupId] = currentGroup
        return result

    def GroupedPhotos(self):
        result = set()
        for photoid,rating in self.photos.items():
            if (rating.Grouped == GroupedEnum.GROUPED):
                result.add(rating.GroupId)
        return list(result)

    def pointToBestOfGroup(self):
        tmp = self.GroupedPhotosPackets()



    def getPreprocessedPhotos(self):
        result = []
        for photoid,rating in self.photos.items():
            if (rating.Status == StatusEnum.GOOD):
                if (rating.Grouped == GroupedEnum.SINGLE):
                    result.append(photoid)
                if (rating.Grouped == GroupedEnum.GROUPED):
                    if photoid == rating.GroupId:
                        result.append(photoid)
        return result

    def rereadFilelist(self, curdir):
        for filename  in os.listdir(curdir):
            if filename.endswith(".jpg") or filename.endswith(".JPG"):
                if not filename in self.photos.keys():
                    self.photos[filename] = PhotoRating(filename)

    def saveRatings(self):
        f = open(self.ratingFilePath, "w")
        for photoid,rating in self.photos.items():
            f.write(photoid+":" + rating.toString() + "\n");
        f.close()

    def calculateStatistics(self):
        self.nbphotos = 0
        self.nbnoTriaged = 0
        self.nbGood = 0
        self.nbnoGrouped = 0
        self.nbGroups = 0
        self.GroupIds = []
        self.nbRatings = 0
        for photoid,rating in self.photos.items():
            self.nbphotos += 1
            if rating.Status  == StatusEnum.UNCHECKED:
                self.nbnoTriaged += 1
            if rating.Status  == StatusEnum.GOOD:
                self.nbGood += 1
            if (rating.Status  == StatusEnum.GOOD) and (rating.Grouped == GroupedEnum.UNCHECKED):
                self.nbnoGrouped += 1
            if rating.Grouped == GroupedEnum.GROUPED:
                if (not rating.GroupId in self.GroupIds):
                    self.nbGroups += 1
                    self.GroupIds.append(rating.GroupId)
            self.nbRatings += rating.ratedcount

    def statistics(self):
        self.calculateStatistics()
        infoStr = "# Photos         : "+ str(self.nbphotos) + "\n"
        infoStr += "# No Triage info : "+ str(self.nbnoTriaged) + "\n"
        infoStr += "# Good           : "+ str(self.nbGood) + "\n"
        infoStr += "# No Group info  : "+ str(self.nbnoGrouped) + "\n"
        infoStr += "# Groups         : "+ str(self.nbGroups) + "\n"

        return infoStr

    def moveAfterSorting(self, numberAllowed):
        if not os.path.exists(self.curdir / 'Bad'):
            bad_dir = self.curdir / 'Bad'
            os.makedirs(str(self.curdir / 'Bad'))

            for photoid,rating in self.photos.items():
                if rating.Status  == StatusEnum.BAD:
                    source_file = self.curdir / photoid
                    dest_file   = bad_dir / photoid
                    if os.path.exists(str(source_file)):
                        os.rename(str(source_file), str(dest_file))


        if not os.path.exists(self.curdir / 'GroupsNotBest'):
            os.makedirs(self.curdir / 'GroupsNotBest')
        for group in self.GroupedPhotos():
            name =  group.split('.')
            if not os.path.exists(self.curdir / "GroupsNotBest" / name[0]):
                groupdir = self.curdir / "GroupsNotBest" / name[0]
                os.makedirs(str(groupdir))
                for photoid,rating in self.photos.items():
                    if (rating.GroupId == group) and not (rating.GroupId == photoid):
                        source_file = self.curdir / photoid
                        dest_file   =  groupdir / photoid
                        if os.path.exists(str(source_file)):
                            os.rename(str(source_file), str(dest_file))

        # TODO move out not in to 25 %
        not_top_dir = self.curdir / ("NotTop-" + str(numberAllowed))
        if not os.path.exists(str(not_top_dir)):
            os.makedirs(str(not_top_dir))
        sortedRatings = self.sortRatings()
        for photonum in range(len(sortedRatings)-1 , numberAllowed, -1):
            sourcefile = self.curdir / sortedRatings[photonum]
            destfile   = not_top_dir / sortedRatings[photonum]
            if (os.path.exists(str(sourcefile))):
                os.rename(str(sourcefile), str(destfile))



    def sortRatings (self):
        # Sort by perceived minimum rating (see Glicko system)
        ratedPhotos = self.getPreprocessedPhotos()
        bestRatings = sorted(ratedPhotos, key=lambda rating:
                Glicko.getMinimalRating(self.photos[rating].mu, self.photos[rating].sigma), reverse=True)
        return bestRatings


from enum import Enum

class StatusEnum(Enum):
    UNCHECKED=0
    GOOD=1
    BAD=2

class GroupedEnum(Enum):
    UNCHECKED=0
    SINGLE=1
    GROUPED=2

class PhotoRating:
    def __init__(self, photoid, string=""):
        self.photoid=photoid
        if (string == ""):
            self.Status     = StatusEnum.UNCHECKED
            self.Grouped    = GroupedEnum.UNCHECKED
            self.mu         = 1500.0
            self.sigma      = 200.0
            self.GroupId    = ""
            self.GroupMu    = 1
            self.GroupSigma = 0
            self.ratedcount = 0
        else:
            self.extractFromString(string)

    def extractFromString(self, string):
        ratingInfo = string.split(',')
        self.Status= StatusEnum(int(ratingInfo[0]))
        self.Grouped= GroupedEnum(int(ratingInfo[1]))
        self.mu          = float(ratingInfo[2])
        self.sigma       = float(ratingInfo[3])
        self.GroupId     = ratingInfo[4]
        self.GroupMu     = int(ratingInfo[5])
        self.GroupSigma  = int(ratingInfo[6])
        self.ratedcount  = int(ratingInfo[7])

    def toString(self):
        result = str(self.Status.value) + "," + \
                 str(self.Grouped.value) + "," + \
                 str(self.mu) + "," + \
                 str(self.sigma) + "," + \
                 str(self.GroupId) + "," + \
                 str(self.GroupMu) + "," + \
                 str(self.GroupSigma) + "," + \
                 str(self.ratedcount)
        return result


