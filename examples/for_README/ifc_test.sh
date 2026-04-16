
CDIR=$(dirname $0)
LOGLEV="INFO"

BACK=$1

python -m pyxhdl.generator \
       --input_file $CDIR/ifc_test.py \
       --entity IfcTest \
       --backend $BACK \
       --inputs "CLK,RST_N=mkreg(BIT)" "A,XOUT=mkreg(UINT16)" \
       --log_level $LOGLEV

