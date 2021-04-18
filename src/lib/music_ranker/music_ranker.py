import math
import nltk

from lib.document_ranker.algorithms.document_ranker import Ranker

class UsageError(Exception):
    pass

class MusicRanker(Ranker):

    # self.k and self.b will need to be tuned
    # In the case of this project, all docs are the same len, so B has no effect.
    # Due to PLN structure, the score increases as K increases, so we can pick anything reasonable.

    # override bm25 method based on the representation we have of the music
    def bm25(self, dwork, cwork):
        # input will be two vectors of the same length representing "term frequency" of each interval
        if len(cwork) != len(dwork):
            raise UsageError("Incorrect usage. Input must be two vectors (lists) of the same length")
        
        score = 0

        for i in range(len(dwork)):
            # ensure the interval is in both works
            if dwork[i] == 0 or cwork[i] == 0:
                continue
            # get the "document frequency" (count of works that contain the target interval)
            doc_freq = 0
            for work in self.corpus:
                # increment doc freq if the work contains the target interval
                if work[i] != 0:
                    doc_freq += 1
            # carefully build each term
            numerator = math.log(1 + math.log(1 + cwork[i]))
            denominator = 1 - self.B + self.B * (float(len(cwork))/self.avdl)
            log_term = math.log((len(self.corpus) + 1) / doc_freq, 10)

            # add the result for the current vector position to score
            score += dwork[i] * (numerator / denominator) * log_term
        return score

    # override the pivoted length normalization method based on the representation we have of the music
    def pivoted_length_normalization(self, dwork, cwork):
        # input will be two vectors of the same length representing "term frequency" of each interval
        if len(cwork) != len(dwork):
            raise UsageError("Incorrect usage. Input must be two vectors (lists) of the same length")
        
        score = 0

        for i in range(len(dwork)):
            # ensure the interval is in both works
            if dwork[i] == 0 or cwork[i] == 0:
                continue
            # get the "document frequency" (count of works that contain the target interval)
            doc_freq = 0
            for work in self.corpus:
                # increment doc freq if the work contains the target interval
                if work[i] != 0:
                    doc_freq += 1
            # carefully build each term
            numerator = (self.K + 1) * cwork[i]
            denominator = cwork[i] + self.K * (1 - self.B + self.B * (float(len(cwork))/self.avdl))
            log_term = math.log((len(self.corpus) + 1) / doc_freq, 10)

            # add the result for the current vector position to score
            score += dwork[i] * (numerator / denominator) * log_term
        return score
