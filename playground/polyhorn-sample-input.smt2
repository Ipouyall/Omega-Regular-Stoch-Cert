(declare-const c_1 Real)
(declare-const c_2 Real)
(declare-const c_3 Real)
(declare-const c_4 Real)

(assert (> (+ c_3 c_4) 0))
(assert (forall ((x Real) ) (=> (and (>= x -1024) (>= 1023 x)) 
    (>= (+ (* c_1 x) c_2) 0) )))
(assert (forall ((x Real) ) (=> (and (>= x -1024) (>= 1023 x) (>= x 1)) 
    (and (>= (+ (* c_1 (+ x -1)) c_2) 0)  (<= (+ (* c_1 (+ x -1)) c_2) (+ (* c_1 x) c_2 -1) ) ))))
(assert (forall ((x Real) ) (=> (and (>= x -1024) (>= 1023 x) (<= x 0)) 
    (and (>= (+ (* c_3 x) c_4) 0) (<= (+ (* c_3 x) c_4 ) (+ (* c_1 x) c_2 -1) ) ))))

(check-sat)
(get-model)


(assert (forall ((x Real)) (= x 3)
    (= (- (+ (* c_1 (* x x)) (* c_2 x)) 12) 0)))