$(document).ready(function() {

    // Logout button
    $('body').on('click', '.logout-button', function(e) {
        e.preventDefault();
        $.ajax({
            url: $(this).attr('href'),
            type: 'GET',
            success: function(response) {
                window.location.href = response.redirect_url;
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
    // Login form
    $('#login-form').on('submit', function(e) {
        e.preventDefault();
        var formData = new FormData(this);
        $.ajax({
            url: $(this).attr('action'),
            type: $(this).attr('method'),
            data: formData,
            processData: false,
            contentType: false,
            success: function(data) {
                if (data.success) {
                    window.location.href = data.redirect_url;
                } else {
                    if (data.error_msg === '로그인 실패! 아이디 또는 비밀번호가 잘못되었습니다.') {
                        $('#errorModalBody').text(data.error_msg);
                        $('#errorModal').modal('show');
                    } else if(data.error_msg === '회원가입 필요'){
                        // 아이디가 존재하지 않을 때 회원가입 여부 모달
                        $('#signupModal').modal('show');
                    }
                }
            },
            error: function(error) {
                console.log(error);
            }
        });
    });


    // Password search form
    $('#search_password-form').on('submit', function(event) {
        event.preventDefault();
        $.ajax({
            url: '/search-password',
            data: $('form').serialize(),
            type: 'POST',
            success: function(response) {
                if (response.success) {
                    alert('비밀번호 힌트: ' + response.password_hint);
                } else {
                    $('#errorMessage').text(response.error_msg);
                    $('#errorModal').modal('show');
                }
            },
            error: function(error) {
                console.log(error);
            }
        });
    });

    // Signup form
    $('#signup-form').on('submit', function(event) {
        event.preventDefault();
        $.ajax({
            url: '/signup',
            data: $(this).serialize(),
            type: 'POST',
            success: function(response) {
                if (response.success) {
                    window.location.href = response.redirect_url;
                } else {
                    alert(response.error_msg);
                }
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
    // Deposit form
    $('#confirm-deposit').on('click', function(e) {
        e.preventDefault();
        var formData = new FormData($('#deposit-form')[0]);

        $.ajax({
            url: '/deposit',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    // Update account balance display here, if necessary
                    alert('입금이 성공적으로 완료되었습니다!');
                    window.location.href = '/';
                } else {
                    alert(response.error_msg);
                }
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
    // Withdraw form
    $('#confirm-withdraw').on('click', function(e) {
        e.preventDefault();
        var formData = new FormData($('#withdraw-form')[0]);

        $.ajax({
            url: '/withdraw',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    // Update account balance display here, if necessary
                    alert('출금이 성공적으로 완료되었습니다!');
                    window.location.href = '/';
                } else {
                    alert(response.error_msg);
                }
            },
            error: function(error) {
                console.log(error);
            }
        });
    });


    // buy coin form confirm-buy-coin
    $('#confirm-buy-coin').on('click', function(e) {
        e.preventDefault();
        var formData = new FormData($('#buy-coin-form')[0]);

        $.ajax({
            url: '/buy-coin',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    // Update account balance display here, if necessary
                    alert('코인 구매가 성공적으로 완료되었습니다!');
                    window.location.href = '/';
                } else {
                    alert(response.error_msg);
                }
            },
            error: function(error) {
                console.log(error);
            }
        });
    });

    $('#confirm-sell-coin').click(function() {
        var coinCount = $('#sell_coin_count').val();
        var price = $('#sell_coin_price').val();

        var data = JSON.stringify({
            sell_coin_count: coinCount,
            sell_coin_price: price
        });

        $.ajax({
            url: '/sell_coin',
            type: 'POST',
            data: data,
            contentType: 'application/json',  // 데이터 형식을 JSON으로 설정
            success: function(response) {
                // POST 요청이 성공한 경우의 처리
                console.log(response);
                // 성공적으로 게시되었음을 사용자에게 알림
                alert('게시글이 성공적으로 게시되었습니다.');
                // 페이지를 새로고침하여 최신 게시글 목록을 표시
                location.reload();
            },
            error: function(error) {
                // POST 요청이 실패한 경우의 처리
                console.log(error);
                // 오류 메시지를 사용자에게 알림
                alert('게시글 게시 중 오류가 발생했습니다. 다시 시도해주세요.');
            }
        });
    });
});
