function myFunction(){
  $('#loading2').hide();
  $('#btn-save').attr('disabled',false);
  $('#btn-edit').attr('disabled','disabled');
  $('#btn-save2').attr('disabled',false);
  $('#btn-edit2').attr('disabled','disabled');
  blockSaveEdit();
}

function blockSaveEdit(option){
  var radio = document.getElementsByClassName("radio-asistencia");
  if(radio){
    if(radio[2].disabled){
      document.getElementById("btn-save").disabled = true;
      document.getElementById("btn-edit").disabled = false;
      document.getElementById("btn-save2").disabled = true;
      document.getElementById("btn-edit2").disabled = false;
    }else{
      document.getElementById("btn-save").disabled = false;
      document.getElementById("btn-edit").disabled = true;
      document.getElementById("btn-save2").disabled = false;
      document.getElementById("btn-edit2").disabled = true;
    } 
  }
  if(option == 1){
    var cmb = document.getElementsByClassName("combo_calificacion");
    if(cmb){
      if(cmb[2].disabled){
        document.getElementById("btn-save").disabled = true;
        document.getElementById("btn-edit").disabled = false;
        document.getElementById("btn-save2").disabled = true;
        document.getElementById("btn-edit2").disabled = false;
      }else{
        document.getElementById("btn-save").disabled = false;
        document.getElementById("btn-edit").disabled = true;
        document.getElementById("btn-save2").disabled = false;
        document.getElementById("btn-edit2").disabled = true;
      }
    }
  }

}

function editar(){
  var comment_box = document.getElementById("comentario-general");
  if(comment_box){
    comment_box.disabled = false;
  }

  var cmb = document.getElementsByClassName("combo_calificacion");
  if(cmb){
    for(i=0;i<cmb.length;i++){
      cmb[i].disabled = false;
    }
  }

  var txt = document.getElementsByClassName("text-obs");
  for(i=0;i<txt.length;i++){
    txt[i].disabled = false;
  }

  var radio = document.getElementsByClassName("radio-asistencia");
  for(i=0;i<radio.length;i++){
    radio[i].disabled = false;
  }
/*
document.getElementById("MyElement").classList.add('MyClass');

document.getElementById("MyElement").classList.remove('MyClass');
*/

	blockSaveEdit();
}

function bloquear(){
  var cmb = document.getElementsByClassName("combo_calificacion");
  if(cmb){
    for(i=0;i<cmb.length;i++){
      cmb[i].disabled = true;
    }
  }

  var comment_box = document.getElementById("comentario-general");
  if(comment_box){
    comment_box.disabled = true;
  }

  var txt = document.getElementsByClassName("text-obs");
  for(i=0;i<txt.length;i++){
    txt[i].disabled = true;
  }

  var radio = document.getElementsByClassName("radio-asistencia");
  for(i=0;i<radio.length;i++){
    radio[i].disabled = true;
  }
}

