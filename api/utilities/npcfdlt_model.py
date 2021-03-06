from api.utilities.spcfdlt_model import SPDLT
from api.utilities.diffusion_model import FixedProbability, ThresholdFunction, QuiescentFunction
from collections import defaultdict

class NPDLT(SPDLT):

    def __init__(self, _g, _tb_rule=FixedProbability(0.5), _t_function=ThresholdFunction(0.1), _q_function=QuiescentFunction(1)):
        super(NPDLT, self).__init__(_g, _tb_rule=_tb_rule, _t_function=_t_function,_q_function=_q_function)

    def run(self):
        self.start()
        switch = 0
        quiescent_nodes = {}
        switch_nodes = []
        deactive = []
        transitions = []
        activation_time  = defaultdict(int)
        previous_size = 0
        # current_size = len(self.active[-1]) + len(self.active[1])
        t = 0
        while t <= 100:
            #  previous_size = current_size
            transitions += [[]]
            trans_list = transitions[-1]
            for v in self.g:

                previous_state = self.activation_state[v]
                if previous_state == SPDLT.QUIESCENT or v in self.seed:
                    continue

                inf_first, inf_second = self.get_influence(v)
                theta = self.compute_threshold(v, activation_time[v], t)

                if inf_second >= theta and inf_first >= theta:
                    # tie breaking rule
                    c = self._tb_rule()
                    next_state = SPDLT.FIRST_CAMPAIGN if c == 0 else SPDLT.SECOND_CAMPAIGN
                elif inf_first >= theta:
                    next_state = SPDLT.FIRST_CAMPAIGN
                elif inf_second >= theta:
                    next_state = SPDLT.SECOND_CAMPAIGN
                else:
                    next_state = SPDLT.INACTIVE

                if previous_state != next_state:
                    if previous_state == SPDLT.INACTIVE:
                        # nuova attivazione
                        self.activation_state[v] = SPDLT.QUIESCENT
                        neg_inf = self.get_negative_influence(v, next_state)
                        q = self.compute_quiescent_time(v, neg_inf)
                        if int(t+q) not in quiescent_nodes:
                            quiescent_nodes[int(t+q)] = []
                        quiescent_nodes[int(t+q)] += [(v, next_state)]
                        trans_list.append(self.transition(v, previous_state, SPDLT.QUIESCENT))
                    elif next_state == SPDLT.INACTIVE:
                        # disatttivazione
                        deactive += [(v, previous_state)]
                    else:
                        #switch
                        switch_nodes += [(v, previous_state, next_state)]
                        switch += 1
                        trans_list.append(self.transition(v, previous_state, next_state))

            # eseguo gli switch
            for u, p, n in switch_nodes:
                self.active[p].remove(u)
                self.active[n].add(u)
                self.activation_state[u] = n
                activation_time[u] = t + 1

            # quiescent -> active
            if quiescent_nodes:
                t = min(quiescent_nodes.keys())
            else:
                break

            for u, c in quiescent_nodes[t]:
                self.activation_state[u] = c
                self.active[c].add(u)
                activation_time[u] = t
                trans_list.append(self.transition(u, SPDLT.QUIESCENT, c))


            # active -> inactive
            for u, c in deactive:
                self.active[c].remove(u)
                self.activation_state[u] = SPDLT.INACTIVE
                activation_time[u] = -1
                trans_list.append(self.transition(u, c, SPDLT.INACTIVE))


            # svuoto la lista
            del deactive[:]
            del quiescent_nodes[t]
            del switch_nodes[:]

        return transitions
