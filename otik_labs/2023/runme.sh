# noexec на флешке #!/bin/bash

RUNSCOUNT='1'
HELPLINE="Запуск: bash ${0} [ b|book|p N|pres -1|-2|-f|--full | -h]"

DOCTYPE='short'

SRCROOTDIR='tex-src'
PRESROOTDIR="${SRCROOTDIR}"
LABSROOTDIR="${SRCROOTDIR}"

SRCFILEFULLNAME=''
BASEFILENAME=''

numargs="$#"
for ((i=1 ; i <= numargs ; i++)); do

  arg="${1}"
  shift
  
  case "$arg" in
  -1)    
    RUNSCOUNT='1'
    ;;
  -2)    
    RUNSCOUNT='2'
    ;;     
  -f|--full)    
    RUNSCOUNT='f'
    ;;     
  b|book)    
    DOCTYPE='book'
    SRCFILEFULLNAME="${LABSROOTDIR}/otik-labs.tex"
    RESFILENAME=otik-labs.pdf
    ;;         
  nb)    
    DOCTYPE='book'
    SRCFILEFULLNAME="${LABSROOTDIR}/otik-labs-nb31.tex"
    RESFILENAME=otik-labs-nb31.pdf
    ;;         
  p|pres)    
    SRCFILEFULLNAME=`ls ${PRESROOTDIR}/${1}_*.tex`
    shift
    ;;
  d)    
    SRCFILEFULLNAME="${1}"
    shift
    #     результат там же, где исходный
    #RESFILENAME=${SRCFILEFULL/.tex/.pdf}
    ;;
        
  -h)
    echo "${HELPLINE}"
    ;;    
  esac  
done

echo $SRCFILEFULLNAME

BASETEXFILENAME=`basename ${SRCFILEFULLNAME}`
BASEFILENAME="${BASETEXFILENAME/.tex/}"
echo $BASEFILENAME

if [[ (-z "${BASEFILENAME}") ]]
then
  echo "Не задано имя файла."
  echo "${HELPLINE}"
  exit
fi

if [[ (-z "${RESFILENAME}") ]]
then
  RESFILENAME=${BASEFILENAME}.pdf
fi

COMPILEDFILE="tmp/${BASEFILENAME}.pdf"

if ! [ -d tmp/ ]; then
  mkdir tmp/
fi

MKTXT="pdflatex --output-directory=tmp ${SRCFILEFULLNAME}"
MKBIB="bibtex tmp/${BASEFILENAME}"


case "$DOCTYPE" in
  book)

  case "$RUNSCOUNT" in
    1)    
      ${MKTXT}
    ;;     
    2)    
      ${MKTXT} &&  ${MKTXT}
    ;;     
#     bib)    
# #         ${MKTXT} && ${MKTXT} && ${MKBIB} && ${MKBIB} && ${MKTXT}&& ${MKTXT}
# 	rm "tmp/${BASEFILENAME}.bbl" "tmp/${BASEFILENAME}.blg"
#         ${MKBIB} && ${MKBIB} && ${MKTXT} # удалять только bib
#     ;;      
    f)        
#       ${MKTXT} &&  ${MKTXT} && ${MKBIB} && ${MKBIB} && ${MKTXT} &&  ${MKTXT}
      if ${MKTXT} 
      then
      
        ${MKTXT} && ${MKBIB} && ${MKBIB} && ${MKTXT}
        
        cd tmp/
        # utf-8 не годится, нужна однобайтовая кодировка (любая подходит, но официально результат rumakeindex в koi8)
        LANG=ru_RU.KOI8-RU rumakeindex ${BASEFILENAME}.idx
        iconv -f KOI8-RU -t WINDOWS-1251 ${BASEFILENAME}.ind -o ${BASEFILENAME}.ind
        cd ..
        
        ${MKTXT} && ${MKTXT}
    
        # ps2pdf -dUseFlatCompression=true ${COMPILEDFILE}
      else
	exit
      fi
    ;;    
  esac  
  
  ;;
  

  
  short)
  case "$RUNSCOUNT" in
    1)    
      ${MKTXT}
    ;;     
    2|f)    
      ${MKTXT} &&  ${MKTXT}
    ;;    
  esac  
  ;;    
  
 
esac # 

echo "Копирую ${COMPILEDFILE} в ${RESFILENAME}..."
cp "${COMPILEDFILE}" "${RESFILENAME}"
