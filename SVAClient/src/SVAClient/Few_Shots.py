SPEC_EXAMPLE_1 = """### Natural Language Problem
Design a circular shift register with parallel load that behaves as follows: the register asynchronously resets to zero when the reset signal is asserted low, loads dataIn when writeEnable is high, otherwise rotates its contents right or left depending on shiftRight. The current register value should be available at the output, and the design should also maintain an internal one-cycle delayed copy of the register.

### Code Implementation
```
module ShiftRegister #(
    parameter Width = 4
) (
    input  logic             clk,
    input  logic             reset_,
    input  logic             shiftRight,
    input  logic             writeEnable,
    input  logic [Width-1:0] dataIn,
    output logic [Width-1:0] dataOut
);

    logic [Width-1:0] shiftRegisters;
    logic [Width-1:0] shiftRegisters_delay1;

    always_ff @(posedge clk, negedge reset_) begin
        if (!reset_) begin
            shiftRegisters <= '0;
        end
        else if (writeEnable) begin
            shiftRegisters <= dataIn;
        end
        else if (shiftRight) begin
            shiftRegisters <= {shiftRegisters[0], shiftRegisters[Width-1:1]};
        end
        else begin
            shiftRegisters <= {shiftRegisters[Width-2:0], shiftRegisters[Width-1]};
        end
    end
    always_ff @(posedge clk, negedge reset_) begin
        if (!reset_) begin
            shiftRegisters_delay1 <= '0;
        end
        else begin
            shiftRegisters_delay1 <= shiftRegisters;
        end
    end
    assign dataOut = shiftRegisters;

endmodule
```

[Response]

### Property 1
In the same cycle that data input is written, the output matches the input.

### Property 2
The total count of ones in the register is invariant to shift operations.

### Property 3
If writeEnable is low and shiftRight is high, dataOut in the next cycle must equal the previous dataOut rotated right by one bit.

### Property 4
If both writeEnable and shiftRight are low, dataOut in the next cycle must equal the previous dataOut rotated left by one bit.

### Property 5
If data is loaded and no further writes occur, the register contents must only change due to rotations.

### Property 6
During rotations, the bit that moves out of one end must correctly appear at the other end.

"""

SPEC_EXAMPLE_2 = """### Natural Language Problem
Design a program counter module in Verilog that increments its address by 1 every clock cycle when the enable signal is high. The program counter should have an 8-bit address.

### Code Implementation
```
module counter(pc_addr, clock, rst, en);
input clock, rst, en;
output reg [7:0] pc_addr;
always @(posedge clock or negedge rst) begin
        if(!rst) begin
                pc_addr <= 8'd0;
        end
        else begin
                if(en) pc_addr <= pc_addr+1;
                else pc_addr <= pc_addr;
        end
end
endmodule
```

[Response]

### Property 1
When the counter is enabled and below its maximum value, it must increment on the next clock edge.

### Property 2
When the counter reaches its maximum value and the enable signal is high, it must reset to zero in the next cycle.

### Property 3
When disabled, the counter must hold its value.

"""

SPEC_EXAMPLE_3 = """### Natural Language Problem
Implement a Verilog module for UART loopback functionality. The module should capture the rising edge of the receive done signal and initiate sending of received data when the UART module is ready to transmit. The module should also include a delay of two clock cycles for the send enable signal.

### Code Implementation
```
module uart_loop(
    input            sys_clk,
    input            sys_rst_n,
    input            recv_done,
    input      [7:0] recv_data,
    input            tx_busy,
    output           recv_done_flag,
    output reg       tx_ready,
    output reg       send_en,
    output reg [7:0] send_data
    );
reg recv_done_d0;
reg recv_done_d1;

assign recv_done_flag = (~recv_done_d1) & recv_done_d0;
always @(posedge sys_clk or negedge sys_rst_n) begin         
    if (!sys_rst_n) begin
        recv_done_d0 <= 1'b0;                                  
        recv_done_d1 <= 1'b0;
    end                                                      
    else begin                                               
        recv_done_d0 <= recv_done;                               
        recv_done_d1 <= recv_done_d0;                            
    end
end
always @(posedge sys_clk or negedge sys_rst_n) begin         
    if (!sys_rst_n) begin
        tx_ready  <= 1'b0; 
        send_en   <= 1'b0;
        send_data <= 8'd0;
    end                                                      
    else begin                                               
        if(recv_done_flag)begin
            tx_ready  <= 1'b1;
            send_en   <= 1'b0;
            send_data <= recv_data;
        end
        else if(tx_ready && (~tx_busy)) begin
            tx_ready <= 1'b0;
            send_en  <= 1'b1;
        end
    end
end
endmodule 
```

[Response]

### Property 1
If recv_done is low now and high in the next cycle, then recv_done_flag must be high two clock cycle later.

### Property 2
If recv_done_flag is high, then tx_ready must be high in the next cycle.

### Property 3
If recv_done_flag is high, then send_data in the next cycle must equal the current value of recv_data.

### Property 4
If tx_ready is high, recv_done_flag is low, and tx_busy is low now, then send_en must be high in the next cycle.

### Property 5
send_en and tx_ready must never be high at the same time.

"""

NL2SVA_HUMAN_EXAMPLE_SEQUENTIAL = '''asrt: assert property (@(posedge clk) disable iff (tb_reset)
    (a && b) != 1'b1
);'''

NL2SVA_HUMAN_EXAMPLE_CLK_ONLY = '''asrt: assert property (@(posedge clk) 
    (a && b) != 1'b1
);'''

NL2SVA_HUMAN_EXAMPLE_COMBINATORIAL = '''asrt: assert property (
    (a && b) != 1'b1
);'''

SVA2NL_EXAMPLE_1 = """### Hardware Design
```
module ShiftRegister #(
  parameter Width = 4
) (
  input  logic             clk,
  input  logic             reset_,
  input  logic             shiftRight,
  input  logic             writeEnable,
  input  logic [Width-1:0] dataIn,
  output logic [Width-1:0] dataOut
);

  logic [Width-1:0] shiftRegisters;
  logic [Width-1:0] shiftRegisters_delay1;

  logic tb_reset = (reset_ == 1'b0)
  always_ff @(posedge clk, negedge reset_) begin
    if (!reset_) begin
      shiftRegisters <= '0;
    end
    else if (writeEnable) begin
        shiftRegisters <= dataIn;
    end
    else if (shiftRight) begin
      shiftRegisters <= {shiftRegisters[0], shiftRegisters[Width-1:1]};
    end
    else begin
      shiftRegisters <= {shiftRegisters[Width-2:0], shiftRegisters[Width-1]};
    end
  end
  always_ff @(posedge clk, negedge reset_) begin
    if (!reset_) begin
      shiftRegisters_delay1 <= '0;
    end
    else begin
      shiftRegisters_delay1 <= shiftRegisters;
    end
  end
  assign dataOut = shiftRegisters;
endmodule
```

### SystemVerilog Assertion (SVA)
```
asrt_io: assert property (@(posedge clk) disable iff (tb_reset)
    (writeEnable && (dataIn != dataOut) !== 1'b1)
);
```

[Response]
In the same cycle that data input is written, the output matches the input.

"""

SVA2NL_EXAMPLE_2 = """### Hardware Design
```
module incrementor(input B, clk, rst, output reg[3:0] out);
reg push_f;
reg push_sync; 
reg push_sync_f; 
wire push_edge; 
    always @(posedge clk) begin
    push_f <= B;
    push_sync <= push_f;
    end
    always @ (posedge clk) begin
    if(rst)
    push_sync_f <= 0;
    else 
    push_sync_f <= push_sync;
    end
    assign push_edge = push_sync & ~push_sync_f;
    always @ (posedge clk) begin
    if(rst)
    out <= 0;
    if(push_edge)begin
        if( out!=9 )begin
            out <= out+1;
            end
        else begin
        out<=0;
        end
     end
  end
endmodule 
```

### SystemVerilog Assertion (SVA)
```
asrt_overflow: assert property (@(posedge clk) disable iff (tb_reset)
    (push_sync && !push_sync_f && out == 9) |=> (out == 0)
);
```

[Response]
If the push button goes high while the output is 9, the output must reset to zero on the next cycle.

"""

SVA2NL_EXAMPLE_3 = """### Hardware Design
```
module CH3_PIEZO_EX(
	RESETN, CLK,
	KEY,
	PIEZO
);
input RESETN, CLK;
input [7:0] KEY;
output PIEZO;
reg BUFF;
integer CNT_SOUND;
integer LIMIT;
wire PIEZO;
always @(KEY)
begin
	case(KEY)
		8'b10000000: LIMIT = 190;
		8'b01000000: LIMIT = 169;
		8'b00100000: LIMIT = 151;
		8'b00010000: LIMIT = 142;
		8'b00001000: LIMIT = 127;
		8'b00000100: LIMIT = 113;
		8'b00000010: LIMIT = 100;
		8'b00000001: LIMIT = 95;
		default: LIMIT = 0;
	endcase
end
always @(posedge CLK)
begin
if(~RESETN)
	begin
		BUFF = 1'b0;
		CNT_SOUND = 0;
	end
else
	begin
		if(CNT_SOUND >= LIMIT)
			begin
				CNT_SOUND = 0;
				BUFF = ~BUFF;
			end
		else
			CNT_SOUND = CNT_SOUND + 1;
	end
end
assign PIEZO = BUFF;
endmodule
```

### SystemVerilog Assertion (SVA)
```
asrt_piezo_toggle: assert property (@(posedge CLK) disable iff (tb_reset)
    ($changed(KEY) && (KEY != 8'b0)) |-> ##[0:$] (BUFF != $past(BUFF))
);
```

[Response]
When a key is pressed, the buzzer drive signal (PIEZO) will eventually toggle.

"""

SVA2NL_MACHINE_EXAMPLE_1 = """### SystemVerilog Assertion (SVA)
```
assert property(@(posedge clk)
    (~|sig_F || sig_C) |-> ##3 sig_A
);
```

### Testbench
```
module testbench (
    input clk,
    input [5:0] sig_A,
    input [5:0] sig_C,
    input [5:0] sig_F
);
endmodule
```

[Response]
If the (bitwise-NOR reduction of sig_F) or sig_C is nonzero, then sig_A should be nonzero after three cycles.
"""

SVA2NL_MACHINE_EXAMPLE_2 = """### SystemVerilog Assertion (SVA)
```
assert property(@(posedge clk)
    (^sig_A) |=> $changed(sig_E)
);
```

### Testbench
```
module testbench (
    input clk,
    input [3:0] sig_A,
    input [3:0] sig_E,
);
endmodule
```

[Response]
If sig_A has an odd number of bits set to 1, then sig_E will change in the next clock cycle.
"""

SVA2NL_MACHINE_EXAMPLE_3 = """### SystemVerilog Assertion (SVA)
```
assert property(@(posedge clk)
    (((sig_J && sig_I) === sig_F) === 1'b1)
);
```

### Testbench
```
module testbench (
    input clk,
    input [7:0] sig_F,
    input [7:0] sig_I,
    input [7:0] sig_J,
);
endmodule
```

[Response]
The logic AND of sig_J and sig_I equals sig_F.
"""

SVA2NL_MACHINE_EXAMPLE_4 = """### SystemVerilog Assertion (SVA)
```
assert property(@(posedge clk)
    (sig_C == sig_A) |-> strong(##[0:$] (sig_B >= sig_D))
);
```

### Testbench
```
module testbench (
    input clk,
    input [6:0] sig_A,
    input [6:0] sig_B,
    input [6:0] sig_C,
    input [6:0] sig_D,
);
endmodule
```

[Response]
When sig_C equals sig_A, sig_B eventually becomes greater than or equal to sig_D.
"""

SVA2NL_EXAMPLE_NO_DUT_1 = """### SystemVerilog Assertion (SVA)
```
asrt_io: assert property (@(posedge clk) disable iff (tb_reset)
    (writeEnable && (dataIn != dataOut) !== 1'b1)
);
```

[Response]
The writeEnable signal is asserted and dataOut matches dataIn.

"""

SVA2NL_EXAMPLE_NO_DUT_2 = """### SystemVerilog Assertion (SVA)
```
asrt_overflow: assert property (@(posedge clk) disable iff (tb_reset)
    (push_sync && !push_sync_f && out == 9) |=> (out == 0)
);
```

[Response]
If push_sync is high and push_sync_f is low while out equals 9 in the current cycle, then out should be set to 0 in the next cycle.

"""

SVA2NL_EXAMPLE_NO_DUT_3 = """### SystemVerilog Assertion (SVA)
```
asrt_piezo_toggle: assert property (@(posedge CLK) disable iff (tb_reset)
    ($changed(KEY) && (KEY != 8'b0)) |-> ##[0:$] (BUFF != $past(BUFF))
);
```

[Response]
When KEY changes value and the new value is not 8'b0, BUFF will eventually change value.

"""

SVA2NL_EXAMPLE_NO_DUT_4 = """### SystemVerilog Assertion (SVA)
```
asrt_upd_rdy_pulse: assert property (@(posedge clk) disable iff (tb_reset)
    upd_rdy |=> (upd_vld || !upd_rdy)
);
```

[Response]
upd_rdy must be a one cycle pulse except next cycle upd_vld is valid.

"""

##########################################################

SVA2WAVEDROM_EXAMPLE_1 = """### SystemVerilog Assertion (SVA)
```
asrt_overflow: assert property (@(posedge clk) disable iff (tb_reset)
    (push_sync && out == 9) |=> (out == 0)
);
```

[Response]
```wavedrom
{
  signal: [
    {name: "clk", wave: "p...."},
    {name: "push_sync", wave: "0.10.", node: "..a"},
    {name: "out", "wave": "x.==x", "data": ["9", "0"], node: "..cd"}
  ],
  head: {
    tick: 0,
    every: 1
  },
  edge: [
    "a->d",
    "b->d",
    "c->d"
  ]
}
```
"""

SVA2WAVEDROM_EXAMPLE_2 = """### SystemVerilog Assertion (SVA)
```
asrt_piezo_toggle: assert property (@(posedge CLK) disable iff (tb_reset)
    ($changed(KEY) && (KEY != 8'b0)) |-> ##[0:$] (BUFF != $past(BUFF))
);
```

[Response]
```wavedrom
{
  signal: [
    {name: "clk", wave: "p..."},
    {name: "KEY", wave: "=x|.", data: ["8'b0"], node: ".a"},
    {name: "BUFF", wave: "x.|=", node: "...b"}
  ],
  head: {
    tick: 0,
    every: 1
  },
  edge: [
    "a~>b",
  ]
}
```
"""

SVA2WAVEDROM_EXAMPLE_3 = """### SystemVerilog Assertion (SVA)
```
asrt_upd_rdy_pulse: assert property (@(posedge clk) disable iff (tb_reset)
    upd_rdy |=> (upd_vld || !upd_rdy)
);
```

[Response]
```wavedrom
{
  signal: [
    {name: "clk", wave: "p......"},
    {name: "upd_vld", wave: "0.10...", node: "..a.c"},
    {name: "upd_rdy", wave: "01x010.", node: "..b.de"},
  ],
  head: {
    tick: 0,
    every: 1
  },
  edge: [
    "a->b",
    "c->e",
    "d->e"
  ]
}
```
"""

SVA2WAVEDROM_EXAMPLE_4 = """### SystemVerilog Assertion (SVA)
```
assert property(@(posedge clk) disable iff (tb_reset)
    (C == A) |-> ##[3:5] (B >= D)
);
```

[Response]
```wavedrom
{
  signal: [
    {name: "clk", wave: "p......"},
    {name: "A", wave: "x==..|x", node: ".a", data: ["a", "3~5 cycles"]},
    {name: "C", wave: "x==..|x", node: ".c", data: ["a"]},
    {name: "D", wave: "x....|=", node: "......d", data: ["d"]},
    {name: "B", wave: "x....|=", node: "......b", data: [">=d"]},
  ],
  head: {
    tick: 0,
    every: 1
  },
  edge: [
    "c~>d"
  ]
}
```
"""

##########################################################

SVA2WAVEDROM_WITH_NL_TB_EXAMPLE_1 = """### Hardware Design
```
module incrementor(input B, clk, rst, output reg[3:0] out);
reg push_f;
reg push_sync; 
reg push_sync_f; 
wire push_edge; 
    always @(posedge clk) begin
    push_f <= B;
    push_sync <= push_f;
    end
    always @ (posedge clk) begin
    if(rst)
    push_sync_f <= 0;
    else 
    push_sync_f <= push_sync;
    end
    assign push_edge = push_sync & ~push_sync_f;
    always @ (posedge clk) begin
    if(rst)
    out <= 0;
    if(push_edge)begin
        if( out!=9 )begin
            out <= out+1;
            end
        else begin
        out<=0;
        end
     end
  end
endmodule 
```

### Natural-Language Property
If the push button goes high while the output is 9, the output must reset to zero on the next cycle.

### SystemVerilog Assertion (SVA)
```
asrt_overflow: assert property (@(posedge clk) disable iff (tb_reset)
    (push_sync && out == 9) |=> (out == 0)
);
```

[Response]
```wavedrom
{
  signal: [
    {name: "clk", wave: "p...."},
    {name: "push_sync", wave: "0.10.", node: "..a"},
    {name: "out", "wave": "x.==x", "data": ["9", "0"], node: "..cd"}
  ],
  head: {
    tick: 0,
    every: 1
  },
  edge: [
    "a->d",
    "b->d",
    "c->d"
  ]
}
```
"""

SVA2WAVEDROM_WITH_NL_TB_EXAMPLE_2 = """### Hardware Design
```
module CH3_PIEZO_EX(
	RESETN, CLK,
	KEY,
	PIEZO
);
input RESETN, CLK;
input [7:0] KEY;
output PIEZO;
reg BUFF;
integer CNT_SOUND;
integer LIMIT;
wire PIEZO;
always @(KEY)
begin
	case(KEY)
		8'b10000000: LIMIT = 190;
		8'b01000000: LIMIT = 169;
		8'b00100000: LIMIT = 151;
		8'b00010000: LIMIT = 142;
		8'b00001000: LIMIT = 127;
		8'b00000100: LIMIT = 113;
		8'b00000010: LIMIT = 100;
		8'b00000001: LIMIT = 95;
		default: LIMIT = 0;
	endcase
end
always @(posedge CLK)
begin
if(~RESETN)
	begin
		BUFF = 1'b0;
		CNT_SOUND = 0;
	end
else
	begin
		if(CNT_SOUND >= LIMIT)
			begin
				CNT_SOUND = 0;
				BUFF = ~BUFF;
			end
		else
			CNT_SOUND = CNT_SOUND + 1;
	end
end
assign PIEZO = BUFF;
endmodule
```

### Natural-Language Property
When a key is pressed, the buzzer drive signal (PIEZO) will eventually toggle.

### SystemVerilog Assertion (SVA)
```
asrt_piezo_toggle: assert property (@(posedge CLK) disable iff (tb_reset)
    ($changed(KEY) && (KEY != 8'b0)) |-> ##[0:$] (BUFF != $past(BUFF))
);
```

[Response]
```wavedrom
{
  signal: [
    {name: "clk", wave: "p..."},
    {name: "KEY", wave: "=x|.", data: ["8'b0"], node: ".a"},
    {name: "BUFF", wave: "x.|=", node: "...b"}
  ],
  head: {
    tick: 0,
    every: 1
  },
  edge: [
    "a~>b",
  ]
}
```
"""

SVA2WAVEDROM_WITH_NL_TB_EXAMPLE_3 = """### Hardware Design
```
module upd_rdy_ctrl (
    input  clk,
    input  reset,
    input  upd_vld,
    input  gen_upd_rdy,
    output reg upd_rdy
);
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            upd_rdy <= 1'b0;
        end else begin
            if (upd_rdy) begin
                upd_rdy <= 1'b0;
            end else begin
                if (gen_upd_rdy) begin
                    upd_rdy <= 1'b1;
                end
            end
        end
    end
endmodule
```

### Natural-Language Property
upd_rdy must be a one cycle pulse except next cycle upd_vld is valid.

### SystemVerilog Assertion (SVA)
```
asrt_upd_rdy_pulse: assert property (@(posedge clk) disable iff (tb_reset)
    upd_rdy |=> (upd_vld || !upd_rdy)
);
```

[Response]
```wavedrom
{
  signal: [
    {name: "clk", wave: "p......"},
    {name: "upd_vld", wave: "0.10...", node: "..a.c"},
    {name: "upd_rdy", wave: "01x010.", node: "..b.de"},
  ],
  head: {
    tick: 0,
    every: 1
  },
  edge: [
    "a->b",
    "c->e",
    "d->e"
  ]
}
```
"""

SVA2WAVEDROM_WITH_NL_TB_EXAMPLE_4 = """### Hardware Design
```
module testbench (
    input  clk,
    input  reset,

    input  [31:0] A,
    input  [31:0] C,
    input  [31:0] B,
    input  [31:0] D
);
// TODO: Check B >= D
endmodule
```

### Natural-Language Property
If at some cycle the signal C equals to signal A, then at some cycle between 3 and 5 cycles later, B >= D must hold.

### SystemVerilog Assertion (SVA)
```
assert property(@(posedge clk) disable iff (tb_reset)
    (C == A) |-> ##[3:5] (B >= D)
);
```

[Response]
```wavedrom
{
  signal: [
    {name: "clk", wave: "p......"},
    {name: "A", wave: "x==..|x", node: ".a", data: ["a", "3~5 cycles"]},
    {name: "C", wave: "x==..|x", node: ".c", data: ["a"]},
    {name: "D", wave: "x....|=", node: "......d", data: ["d"]},
    {name: "B", wave: "x....|=", node: "......b", data: [">=d"]},
  ],
  head: {
    tick: 0,
    every: 1
  },
  edge: [
    "c~>d"
  ]
}
```
"""

##########################################################