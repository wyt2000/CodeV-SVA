# Usage: python test_server.py verify

import requests
import sys

test_func = sys.argv[1] if len(sys.argv) > 1 else "syntax"

if test_func == "syntax":
    url = "http://127.0.0.1:4422/syntax"
    data = {
        "impl": '''`timescale 10ns / 10ns
module accumulator  #(
    parameter       E_BITS  =   16
)
(
    input   wire    [E_BITS-1:0]    i_mux   ,
    input   wire        i_clock ,   i_reset ,
    input   wire                    enable  ,
    output  reg     [E_BITS-1:0]    o_acc
);
always  @(negedge i_clock)
    begin
        if(i_reset)
            o_acc       <=      16'b0        ;
        else if  (enable)
            o_acc       <=      i_mux        ;
    end
endmodule'''
    }
elif test_func == "parse":
    url = "http://127.0.0.1:4422/svparse"
    data = {
        "impl": '''module IDE(
    input [23:12] ADDR,
    input RW,
    input AS_n,
    input CLK,
    input ide_access,
    input IORDY,
    input ide_enable,
    input RESET_n,
    output IDECS1_n,
    output IDECS2_n,
    output IDEBUF_OE,
    output IDE_ROMEN
    );
reg ide_enabled;
assign IDECS1_n = !(ide_access && ADDR[12] && !ADDR[16]) || !ide_enabled;
assign IDECS2_n = !(ide_access && ADDR[13] && !ADDR[16]) || !ide_enabled;
assign IDE_ROMEN = !(ide_access && (!ide_enabled || ADDR[16]));
assign IDEBUF_OE = !(ide_access && ide_enabled && !ADDR[16] && (!AS_n || !RW));
always @(posedge CLK or negedge RESET_n) begin
  if (!RESET_n) begin
    ide_enabled <= 0;
  end else begin
    if (ide_access && ide_enable && !RW) ide_enabled <= 1;
  end
end
endmodule'''
    }
elif test_func == "cov":
    url = "http://127.0.0.1:4422/cov"
    data = {
        "sv": '''module ShiftRegister (
input  logic             clk,
input  logic             reset_,
input  logic             shiftRight,
input  logic             writeEnable,
input  logic [3:0] dataIn,
output logic [3:0] dataOut,
output logic tb_reset
);

logic [3:0] shiftRegisters;
assign tb_reset = (reset_ == 1'b0);

always_ff @(posedge clk, negedge reset_) begin
if (!reset_) begin
    shiftRegisters <= '0;
end
else if (writeEnable) begin
    shiftRegisters <= dataIn;
end
else if (shiftRight) begin
    shiftRegisters <= {shiftRegisters[0], shiftRegisters[3:1]};
end
else begin
    shiftRegisters <= {shiftRegisters[4-2:0], shiftRegisters[3]};
end
end

assign dataOut = shiftRegisters;

endmodule''',
        "sva": '''module ShiftRegister_tb (
input clk,
input reset_,
input shiftRight,
input writeEnable,
input [3:0] dataIn,
input [3:0] dataOut,
input tb_reset
);

asrt: assert property (@(posedge clk) disable iff (tb_reset)
(writeEnable && (dataIn != dataOut) !== 1'b1)
);

endmodule

bind ShiftRegister ShiftRegister_tb ShiftRegister_tb_inst (.*);''',
        "clock": "clk",
        "reset": "reset_"
    }
elif test_func == "verify":
    url = "http://127.0.0.1:4422/verify"
    data = {
        "impl": '''module ShiftRegister (
  input  logic             clk,
  input  logic             reset_,
  input  logic             shiftRight,
  input  logic             writeEnable,
  input  logic [3:0] dataIn,
  output logic [3:0] dataOut,
  output logic tb_reset
);

  logic [3:0] shiftRegisters;
  assign tb_reset = (reset_ == 1'b0);

  always_ff @(posedge clk, negedge reset_) begin
    if (!reset_) begin
      shiftRegisters <= '0;
    end
    else if (writeEnable) begin
        shiftRegisters <= dataIn;
    end
    else if (shiftRight) begin
      shiftRegisters <= {shiftRegisters[0], shiftRegisters[3:1]};
    end
    else begin
      shiftRegisters <= {shiftRegisters[4-2:0], shiftRegisters[3]};
    end
  end

  assign dataOut = shiftRegisters;
  
endmodule

module ShiftRegister_top (
  input  logic             clk,
  input  logic             reset_,
  input  logic             shiftRight,
  input  logic             writeEnable,
  input  logic [3:0] dataIn,
  output logic [3:0] dataOut,
  output logic tb_reset
);

    ShiftRegister ShiftRegister_inst (
        .clk        (clk),
        .reset_     (reset_),
        .shiftRight (shiftRight),
        .writeEnable(writeEnable),
        .dataIn     (dataIn),
        .dataOut    (dataOut),
        .tb_reset   (tb_reset)
    );
  
endmodule''',
        "tb": '''module ShiftRegister_tb (
input clk,
input reset_,
input shiftRight,
input writeEnable,
input [3:0] dataIn,
input [3:0] dataOut,
input tb_reset
);

endmodule

bind ShiftRegister_top ShiftRegister_tb ShiftRegister_tb_inst (.*);''',
        "asrt": '''asrt: assert property (@(posedge clk) disable iff (tb_reset)
(writeEnable && (dataIn != dataOut) !== 1'b1)
);''',
        "clock": "clk",
        "reset": "(${top}_tb_inst.tb_reset)",
        "top_name": "ShiftRegister",
    }
elif test_func == "verify_infer":
    url = "http://127.0.0.1:4422/verify"
    data = {
        "impl": '''module ShiftRegister (
  input  logic             clk,
  input  logic             reset_,
  input  logic             shiftRight,
  input  logic             writeEnable,
  input  logic [3:0] dataIn,
  output logic [3:0] dataOut,
  output logic tb_reset
);

  logic [3:0] shiftRegisters;
  assign tb_reset = (reset_ == 1'b0);

  always_ff @(posedge clk, negedge reset_) begin
    if (!reset_) begin
      shiftRegisters <= '0;
    end
    else if (writeEnable) begin
        shiftRegisters <= dataIn;
    end
    else if (shiftRight) begin
      shiftRegisters <= {shiftRegisters[0], shiftRegisters[3:1]};
    end
    else begin
      shiftRegisters <= {shiftRegisters[4-2:0], shiftRegisters[3]};
    end
  end

  assign dataOut = shiftRegisters;
  
endmodule''',
        "tb": '''module ShiftRegister_tb (
input clk,
input reset_,
input shiftRight,
input writeEnable,
input [3:0] dataIn,
input [3:0] dataOut,
input tb_reset
);

endmodule

bind ShiftRegister ShiftRegister_tb ShiftRegister_tb_inst (.*);''',
        "asrt": '''asrt: assert property (@(posedge clk) disable iff (tb_reset)
(writeEnable && (dataIn != dataOut) !== 1'b1)
);''',
        "top_name": "ShiftRegister",
    }

elif test_func == "verify_impl_only":
    url = "http://127.0.0.1:4422/verify_impl_only"
    data = {
        "impl": '''module ShiftRegister (
  input  logic clk,
  input  logic reset_,
  input  logic shiftRight,
  input  logic writeEnable,
  input  logic [3:0] dataIn,
  output logic [3:0] dataOut
);

  logic [3:0] shiftRegisters;

  always_ff @(posedge clk, negedge reset_) begin
    if (!reset_) begin
      shiftRegisters <= '0;
    end
    else if (writeEnable) begin
        shiftRegisters <= dataIn;
    end
    else if (shiftRight) begin
      shiftRegisters <= {shiftRegisters[0], shiftRegisters[3:1]};
    end
    else begin
      shiftRegisters <= {shiftRegisters[4-2:0], shiftRegisters[3]};
    end
  end

  assign dataOut = shiftRegisters;
  
endmodule

module ShiftRegister_tb (
    input clk,
    input reset_,
    input shiftRight,
    input writeEnable,
    input [3:0] dataIn,
    input [3:0] dataOut
);

endmodule

bind ShiftRegister ShiftRegister_tb ShiftRegister_test (.*);
''',
    "top_name": "ShiftRegister",
    "clock": "clk",
    "reset": "reset_",
    "asrt": '''asrt: assert property (@(posedge clk) disable iff (tb_reset)
(writeEnable && (dataIn != dataOut) !== 1'b1)
);''',
    "reset_polarity": False,
}

elif test_func == "verify_comb":
    url = "http://127.0.0.1:4422/verify"
    data = {
        "impl": '''module ShiftRegister (
  input  logic [3:0] dataIn,
  output logic [3:0] dataOut
);
  assign dataOut = dataIn;
endmodule''',
        "tb": '''module ShiftRegister_tb (
input [3:0] dataIn,
input [3:0] dataOut
);
endmodule
bind ShiftRegister ShiftRegister_tb ShiftRegister_tb_inst (.*);''',
        "asrt": '''asrt: assert property (dataIn == dataOut);''',
    }
elif test_func == "equal":
    url = "http://127.0.0.1:4422/equal"
    data = {
        "key_signal" : "tb_reset",
        "asrt": '''asrt: assert property (@(posedge clock) disable iff (tb_reset)
    result == pixel[127]
);
''',
        "ref_asrt": '''asrt: assert property (@(posedge clock) disable iff (tb_reset)
    result == pixel[127]
);
''',
        "tb": '''module shifter_128bit
    (
        output result,
        input [127:0] load_val,
        input load_n, 
        input shift, 
        input reset, 
        input clock
    );
    reg [127:0] pixel;
    assign result = pixel[127];
    always @(posedge clock)
    begin 
        if(reset == 1'b1)
            pixel <= {128{1'b0}};
        else if (load_n == 1'b1)
            pixel <= load_val;
        else if (shift == 1'b1)
            pixel <= pixel << 1;
    end

    wire tb_reset;
    assign tb_reset = (reset == 1'b1);
// TODO: ASSERTION
endmodule
''',
    }
elif test_func == "mvote":
    url = "http://127.0.0.1:4422/mvote"
    data = {
        "key_signal" : "tb_reset",
        "signal_list": "[2:0] current_state, [2:0] next_state, sda_in, IDLE, START_STATE, SCL, tb_reset",
        "asrts": ["asrt_0: assert property (@(posedge SCL) disable iff (tb_reset)\n    (sda_in == sda_in)\n);", "asrt_1: assert property (@(posedge SCL) disable iff (tb_reset) 1'b1==1'b1);", "asrt_2: assert property (@(posedge SCL) disable iff (tb_reset) 1'b1);", "asrt_3: assert property (@(posedge SCL) disable iff (tb_reset) 1'b0);"],
        "tb": "module test(\n    input [2:0] current_state,\n    input [2:0] next_state,\n    input sda_in,\n    input IDLE,\n    input START_STATE,\n    input SCL,\n    input tb_reset\n);\n\nendmodule"
    }
elif test_func == "mvote_infer":
    url = "http://127.0.0.1:4422/mvote"
    data = {
        "key_signal" : "tb_reset",
        "asrts": ["asrt_0: assert property (@(posedge SCL) disable iff (tb_reset)\n    (sda_in == sda_in)\n);", "asrt_1: assert property (@(posedge SCL) disable iff (tb_reset) 1'b1==1'b1);", "asrt_2: assert property (@(posedge SCL) disable iff (tb_reset) 1'b1);", "asrt_3: assert property (@(posedge SCL) disable iff (tb_reset) 1'b0);"],
        "tb": "module test(\n    input [2:0] current_state,\n    input [2:0] next_state,\n    input sda_in,\n    input IDLE,\n    input START_STATE,\n    input SCL,\n    input tb_reset\n);\n\nendmodule"
    }
elif test_func == "testbench":
    url = "http://127.0.0.1:4422/testbench"
    data = {
        "impl": '''`timescale 10ns / 10ns
module accumulator  #(
    parameter       E_BITS  =   16 
)
(
    input   wire    [E_BITS-1:0]    i_mux   ,
    input   wire        i_clock ,   i_reset ,
    input   wire                    enable  ,
    output  reg     [E_BITS-1:0]    o_acc  
);
always  @(negedge i_clock)
    begin  
        if(i_reset)
            o_acc       <=      16'b0        ;      
        else if  (enable)
            o_acc       <=      i_mux        ;      
    end    
endmodule'''
    }

else:
    assert False

headers = {
    "Content-Type": "application/json"
}

import concurrent.futures

def send_request():
    response = requests.post(url, json=data, headers=headers)
    return response

with concurrent.futures.ProcessPoolExecutor(max_workers=1) as executor:
    futures = [executor.submit(send_request) for _ in range(1)]
    for future in concurrent.futures.as_completed(futures):
        response = future.result()
        if response.status_code == 200:
            # print("OK")
            print("Response:")
            print(response.json())
            if 'input_code' in response.json():           
               print(response.json()["input_code"])
            if 'report' in response.json():           
               print(response.json()["report"])
            if 'data' in response.json():           
               print(response.json()["data"])
        else:
            print(f"Error: {response.status_code}, {response.text}")
            if 'traceback' in response.text:
                print("Traceback:")
                print(response.json()['traceback'])
