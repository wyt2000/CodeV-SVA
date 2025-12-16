NL2SVA_HUMAN_EXAMPLE_SEQUENTIAL = '''asrt: assert property (@(posedge clk) disable iff (tb_reset)
    (a && b) != 1'b1
);'''

NL2SVA_HUMAN_EXAMPLE_CLK_ONLY = '''asrt: assert property (@(posedge clk) 
    (a && b) != 1'b1
);'''

NL2SVA_HUMAN_EXAMPLE_COMBINATORIAL = '''asrt: assert property (
    (a && b) != 1'b1
);'''
