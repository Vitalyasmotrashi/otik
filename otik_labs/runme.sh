# noexec на флешке #!/bin/bash

SRCROOTDIR='tex-src'


TEXNAME=''
TEXBASENAME=''
NOEXTTEXBASENAME=''
RESULTPDFNAME=''
RUNSCOUNT='1'
TARGETTYPE='d'
DOSPLIT='0'

HELPLINE="Запуск: bash ${0} b | book | bx | p N | pres N | d texname | i texname   [-1|-2|-f|--full]  [-h]"

numargs="$#"
for ((i=1 ; i <= numargs ; i++)); do

  arg="${1}"
  shift
  
  case "$arg" in
  
  # 1 и 2 — сколько раз pdflatex; f — много pdflatex, а для некоторых типов bibtex + индекс
  -1)    
    RUNSCOUNT='1'
    ;;
  -2)    
    RUNSCOUNT='2'
    ;;     
  -f|--full)    
    RUNSCOUNT='f'
    ;; 
    
  -s|--split)    
    DOSPLIT='1'
    ;; 
    
  # тип документа TARGETTYPE: откуда исходник + как собирать + куда результат
  # ***************************************************************************
  # книга (разные имена, одинаковая сборка): имя исходника и результата фиксировано, f-сборка: pdflatex + bibtex + индекс (1-2 — только pdflatex)
  b|book)    
    TARGETTYPE='b'
#     TEXNAME=${SRCROOTDIR}/book/0main.tex
    TEXNAME=${SRCROOTDIR}/book-2025/0main.tex
    RESULTPDFNAME=otik-labs.pdf
    ;;     
  bx|nextbook)    
    TARGETTYPE='b'
    TEXNAME=${SRCROOTDIR}/book-2025/0main.tex
    RESULTPDFNAME=otik-labs-testing.pdf
    ;;     
  
  # для сборки достаточно pdflatex:
  p|pres)    
    # презентация: имя исходника восстанавливается по номеру, результат в корень под своим именем
    TARGETTYPE='p'
#     TEXNAME=`ls ${SRCROOTDIR}/pres/${1}*`
    TEXNAME=`ls ${SRCROOTDIR}/${1}*`
    shift
    ;;
  d)    
    # документ: имя исходника задано в командной строке, результат в папку исходника
    TARGETTYPE='d'
    TEXNAME="${1}"
    RESULTPDFNAME=${TEXNAME/.tex/.pdf}
    shift
    ;;
  g)
    # документ: имя исходника задано в командной строке, результат в корневую папку
    TARGETTYPE='g'
    TEXNAME="${1}"
    shift
    ;;
  i)  
    # картинка: имя исходника задано в командной строке, обрезка после сборки, результат в захардкоженную папку
    TARGETTYPE='i'
    TEXNAME="${1}"
    shift
    ;;
       
  -h)
    echo "${HELPLINE}"
    ;;    
  esac  
done

echo "${TEXNAME} → ${RESULTPDFNAME}"


TEXBASENAME=`basename ${TEXNAME}`
NOEXTBASEFILENAME="${TEXBASENAME/.tex/}"

echo "${NOEXTBASEFILENAME}"

# для b-типов RESULTPDFNAME уже задано вручную; для d уже рассчитано
case "$TARGETTYPE" in
  p | g)    
    RESULTPDFNAME="${NOEXTBASEFILENAME}.pdf"
    ;;
  i)    
    RESULTPDFNAME="${SRCROOTDIR}/img/${NOEXTBASEFILENAME}.pdf"
    ;;
esac  


echo "→ ${RESULTPDFNAME}"

if [[ (-z "${NOEXTBASEFILENAME}") ]]
then
  echo "Не задано имя файла."
  echo "${HELPLINE}"
  exit
fi


if ! [ -d tmp/ ]; then
  mkdir tmp/
fi

COMPILEDFILE="tmp/${NOEXTBASEFILENAME}.pdf"

MKTXT="pdflatex --output-directory=tmp ${TEXNAME}"
MKBIB="bibtex tmp/${NOEXTBASEFILENAME}"

echo "${MKTXT}, ${MKBIB}"

case "$RUNSCOUNT" in
1)    
    ${MKTXT}
;;     
2)    
    ${MKTXT} && ${MKTXT}
;;     
f)        
    if [[ "${TARGETTYPE}" == "b" ]]; then
      if ${MKTXT} 
      then
      
#         ${MKTXT} && ${MKBIB} && ${MKBIB} && ${MKTXT}
        ${MKBIB} && ${MKBIB} && ${MKTXT} && ${MKTXT}
        
        cd tmp/
        # utf-8 не годится, нужна однобайтовая кодировка (любая подходит, но официально результат rumakeindex в koi8)
        LANG=ru_RU.KOI8-RU rumakeindex ${NOEXTBASEFILENAME}.idx
        iconv -f KOI8-RU -t WINDOWS-1251 ${NOEXTBASEFILENAME}.ind -o ${NOEXTBASEFILENAME}.ind
        cd ..
        
        ${MKTXT} && ${MKTXT}
  
  
        # ps2pdf -dUseFlatCompression=true ${COMPILEDFILE}
      else # не собралось первый раз
        exit
      fi
    else # не b
        ${MKTXT} && ${MKTXT}    
    fi
esac  


if [[ "${TARGETTYPE}" == "i" ]]; then
    pdfcrop --margins=0  "${COMPILEDFILE}" "${COMPILEDFILE}"
fi 

echo "Копирую ${COMPILEDFILE} в ${RESULTPDFNAME}..."
cp "${COMPILEDFILE}" "${RESULTPDFNAME}"


if [[ "${DOSPLIT}" == "1" ]]; then
    pdftk "${RESULTPDFNAME}" burst output "${RESULTPDFNAME/.pdf/}_page%d.pdf"
fi 


# if [[ "${TARGETTYPE}" == "b" ]] && [[ "${RESULTPDFNAME}" == "otik-labs-testing.pdf" ]]; then
#     pdftk otik-labs-testing.pdf cat 6-33 output otik-reglament+2.pdf
# fi 

# if [[ "${TARGETTYPE}" == "b" ]] && [[ "${RESULTPDFNAME}" == "otik-labs.pdf" ]]; then
#     pdftk otik-labs.pdf cat 2-26 output RL01.pdf
#     pdftk otik-labs.pdf cat 23-26 output L1.pdf
#     pdftk otik-labs.pdf cat 27-30 output L2.pdf
#     pdftk otik-labs.pdf cat 31-33 output L3.pdf
#     pdftk otik-labs.pdf cat 34-37 output L4.pdf
#     pdftk otik-labs.pdf cat 38-40 output L5.pdf
# fi 

# if [[ "${TARGETTYPE}" == "b" ]] && [[ "${RESULTPDFNAME}" == "otik-labs.pdf" ]]; then
#     pdftk "${RESULTPDFNAME}" cat 14-38 output RA_RL_L0.pdf
# fi 
