
LOGLEV="INFO"

BACK=$1

python -m pyxhdl.generator \
       --input_file ifc_test.py \
       --entity IfcTest \
       --backend $BACK \
       --inputs "CLK,RST_N=mkreg(BIT)" \
       --inputs "A,XOUT=mkreg(UINT16)" \
       --log_level $LOGLEV

