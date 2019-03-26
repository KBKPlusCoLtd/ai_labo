(function() {
    // 変数定義
    var PIECE_TYPE = {
        'NONE'   : 0,
        'BLACK'  : 1,
        'WHITE'  : 2,
        'MAX'    : 3,
    };
    var stone;
    var board = [];
    var board_size;
    var turn;
    var level;

    // ひっくり返す処理
    var checkTurnOver = function(x, y, flip, t) {

        var ret = 0;

        for (var dx = -1; dx <= 1; dx++) {
            for(var dy = -1; dy <= 1; dy++) {
                if (dx == 0 && dy == 0) {
                    continue;
                }
                var nx = x + dx;
                var ny = y + dy;
                var n = 0;
                while(board[nx][ny] == PIECE_TYPE.MAX - t) {
                    n++;
                    nx += dx;
                    ny += dy;
                }
                if (n > 0 && board[nx][ny] == t) {
                    ret += n;
                    if (flip) {
                        nx = x + dx;
                        ny = y + dy;
                        while(board[nx][ny] == PIECE_TYPE.MAX - t) {
                            board[nx][ny] = t;
                            nx += dx;
                            ny += dy;
                        }
                    }
                }
            }
        }

        return ret;
    };

    // boardの画面表示
    var showBoard = function() {
        board_size = parseInt($('input[name=board]:checked').val());
        turn = parseInt($('input[name=turn]:checked').val());
        level = $('input[name=level]:checked').val();
        var b = document.getElementById("board");

        while(b.firstChild) {
            b.removeChild(b.firstChild);
        }

        for(var y = 1; y <= board_size; y++) {
            for(var x = 1; x <= board_size; x++) {
                var cell = stone[board[x][y]].cloneNode(true);

                cell.style.left = ((x - 1) * 31) + "px";
                cell.style.top = ((y - 1) * 31) + "px";
                b.appendChild(cell);

                if (board[x][y] == PIECE_TYPE.NONE) {
                    (function() {
                        var _x = x;
                        var _y = y;
                        if(checkTurnOver(_x, _y, false, turn) > 0) {
                            cell.classList.add('active');
                        }
                        cell.onclick = function() {
                            if (checkTurnOver(_x, _y, true, turn) > 0) {
                              board[_x][_y] = turn;
                              showBoard();
                              doAjax(_x - 1, _y - 1);
                            }
                        };
                    })();
                }
            }
        }
    };


    // 始めるボタンで初期設定
    $('#btn').click(function() {
      board_size = parseInt($('input[name=board]:checked').val());
      turn = parseInt($('input[name=turn]:checked').val());
      level = $('input[name=level]:checked').val();
      $('.level').hide();
      $('.turn').hide();
      $('.board').hide();
      $('#btn').hide();
      $('#level').text(level);
      if (turn == 1) {
        $('#turn').text('先行');
      } else {
        $('#turn').text('後攻');
      }

      $('.status').show();

      stone = [
          document.getElementById("cell"),
          document.getElementById("black"),
          document.getElementById("white")
      ];

      Object.freeze(PIECE_TYPE);

      for (var i = 0; i < 10; i++) {
          board[i] = [];
          for (var j = 0; j < 10; j++) {
              board[i][j] = PIECE_TYPE.NONE;
          }
      }
      board[board_size / 2][board_size / 2 + 1] = PIECE_TYPE.BLACK;
      board[board_size / 2 + 1][board_size / 2] = PIECE_TYPE.BLACK;
      board[board_size / 2][board_size / 2] = PIECE_TYPE.WHITE;
      board[board_size / 2 + 1][board_size / 2 + 1] = PIECE_TYPE.WHITE;

      showBoard();

      // 後攻の場合いったんAIに打ってもらう
      if(turn == 2) {
        doAjax("", "");
      }
    });


    // Ajax通信結果取得用
    var getResult = function(data) {
      // 取得したstatusごとに処理を行う
      if (data.status == 'win') {
        if (data.agent_place[0].toString() != "") {
          checkTurnOver(data.agent_place[0] + 1, data.agent_place[1] + 1, true, PIECE_TYPE.MAX - turn);
          board[data.agent_place[0] + 1][data.agent_place[1] + 1] = PIECE_TYPE.MAX - turn;
          showBoard();
        }
        setTimeout(function(){
          alert('あなたの勝ちです');
        },300);

        $('.level').show();
        $('.turn').show();
        $('.board').show();
        $('#btn').show();
      } else if (data.status == 'lose') {
        if (data.agent_place[0].toString() != "") {
          checkTurnOver(data.agent_place[0] + 1, data.agent_place[1] + 1, true, PIECE_TYPE.MAX - turn);
          board[data.agent_place[0] + 1][data.agent_place[1] + 1] = PIECE_TYPE.MAX - turn;
          showBoard();
        }
        setTimeout(function(){
          alert('あなたの負けです');
        },300);
        $('.level').show();
        $('.turn').show();
        $('.board').show();
        $('#btn').show();
      } else if (data.status == 'draw') {
        if (data.agent_place[0].toString() != "") {
          checkTurnOver(data.agent_place[0] + 1, data.agent_place[1] + 1, true, PIECE_TYPE.MAX - turn);
          board[data.agent_place[0] + 1][data.agent_place[1] + 1] = PIECE_TYPE.MAX - turn;
          showBoard();
        }
        setTimeout(function(){
          alert('引き分けです');
        },300);

        $('.level').show();
        $('.turn').show();
        $('.board').show();
        $('#btn').show();
      } else if (data.status == 'pass') {
        alert('AIがパスしました');
        if (!($('.active').length)) {
          setTimeout(function(){
            alert('パスします');
          },300);
          doAjax("", "");
        }
      } else if (data.status != 'pass' && data.agent_place != ["",""]) {
        checkTurnOver(data.agent_place[0] + 1, data.agent_place[1] + 1, true, PIECE_TYPE.MAX - turn);
        board[data.agent_place[0] + 1][data.agent_place[1] + 1] = PIECE_TYPE.MAX - turn;
        showBoard();
        if (!($('.active').length)) {
          setTimeout(function(){
            alert('パスします');
          },300);
          doAjax("", "");
          }
        }
      // console.log(data); // デバッグ用
      $('#blackScore').text(data.score[0]);
      $('#whiteScore').text(data.score[1]);
      $('#status').text('');
      if (data.status == 'win') {
        $('#status').text('勝ち');
      } else if (data.status == 'lose') {
        $('#status').text('負け');
      } else if (data.status == 'draw') {
        $('#status').text('引分');
      } else if (data.status == 'pass') {
        $('#status').text('パス');
      }
    }

    // Ajax通信を行う
    var doAjax  = (function(x, y) {
      var form = $(this);
      $.ajax({
        url: 'http://localhost:8000/api/',
        headers: { "X-CSRFToken": getCookie('csrftoken') },
        type: 'post',
        dataType: 'json',
        contentType: 'charset=utf-8',
        data: JSON.stringify({
          "board": getBoard(),
          "player_place":[x, y],
          "level": level,
          "turn": turn,
          "board_size": board_size,
        }),
      })
      .done( function(data) {
        data = JSON.parse(data)
        getResult(data);
      })
    });
  })();

// boardを配列にして取得
var getBoard = (function() {
  var board = [];
  $('#board > .square').each(function() {
    if ($(this).attr('id') == 'cell') {
      board.push(0);
    } else if ($(this).attr('id') == 'black') {
      board.push(1);
    } else if ($(this).attr('id') == 'white') {
      board.push(2);
    }
  });
  return board
});

// using jQuery csrftoken取得用
var getCookie = (function(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i <= cookies.length; i++) {
            var cookie = $.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
});
