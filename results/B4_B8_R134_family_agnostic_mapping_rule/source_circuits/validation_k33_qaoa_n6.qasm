OPENQASM 3.0;
include "stdgates.inc";
gate rzz(p0) _gate_q_0, _gate_q_1 {
  cx _gate_q_0, _gate_q_1;
  rz(p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
}
qubit[6] q;
h q[0];
h q[1];
h q[2];
h q[3];
h q[4];
h q[5];
rzz(pi/7) q[0], q[3];
rzz(pi/7) q[0], q[4];
rzz(pi/7) q[0], q[5];
rzz(pi/7) q[1], q[3];
rzz(pi/7) q[1], q[4];
rzz(pi/7) q[1], q[5];
rzz(pi/7) q[2], q[3];
rzz(pi/7) q[2], q[4];
rzz(pi/7) q[2], q[5];
rx(pi/5) q[0];
rx(pi/5) q[1];
rx(pi/5) q[2];
rx(pi/5) q[3];
rx(pi/5) q[4];
rx(pi/5) q[5];
