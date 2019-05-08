import numpy as np



def nmi_score( list_1,list_2 ):
    
    set_1 = sorted(list(set(list_1)))
    set_2 = sorted(list(set(list_2)))
    
    B1 = len(set(set_1))
    B2 = len(set(set_2))
    
    ## in case the classes are not 0,1,2,3 ...
    dict_set_1 = dict(zip( set_1,np.arange(B1) ))
    dict_set_2 = dict(zip( set_2,np.arange(B2) ))
    
    n_tt = np.zeros((B1,B2))
    
    N = len(list_1)
    for i_n in range(N):
        c1 = list_1[i_n]
        c2 = list_2[i_n]
        
        ind_1 = dict_set_1[c1]
        ind_2 = dict_set_2[c2]
        n_tt[ind_1,ind_2] += 1
    p_tt = n_tt/float(N)
    
    p_t1 = np.sum(p_tt,axis=1)
    p_t2 = np.sum(p_tt,axis=0)
    H1 = sum([-p*np.log(p) for p in p_t1 if p>0.0])
    H2 = sum([-p*np.log(p) for p in p_t2 if p>0.0])
    MI = 0.0
    for i1 in range(B1):
        for i2 in range(B2):
            p1 = p_t1[i1]
            p2 = p_t2[i2]
            p12 = p_tt[i1,i2]
            if p12> 0.0:
                MI+=p12*np.log(p12/(p1*p2))
    NMI = 2.0*MI/(H1+H2)
    if B1==1 and B2 == 1:
        NMI=1
    return NMI