'use strict';

class tfotografii {

	imyafajla(n) {
		return '"original/' + n + '.jpg"';
	}

	kratnost32(i) {
		var a = i % 2 == 0,
			b = i % 3 == 0;

		if (a && b) return '<div class="clearfix visible-sm-block visible-md-block visible-lg-block"></div>';
		if (a) return '<div class="clearfix visible-sm-block"></div>';
		if (b) return '<div class="clearfix visible-md-block visible-lg-block"></div>';
		return '';
	}

	vypusknikia(n, k, c) {
		return '<a href=' + this.imyafajla(n + '-' + k) + ' class="btn btn-circle" data-fancybox="group" data-caption=" ' + c + '">' + k + '</a>';
	}

	vypuskniki(h, x) {
		var a, h1, h2, i, j, k, n1, n2, s,
			t = '<div class="row"><div class="col-md-8 col-md-offset-2"><h3 class="zagolovok-a">' + h + '</h3></div></div><div class="row"><div class="col-md-8 col-md-offset-2"><div class="row">';

		for (i = 0, j = 1; i < x.length; i += 4, j++) {
			n1 = x[i];
			n2 = this.imyafajla(n1);
			h1 = x[i + 1];
			h2 = x[i + 2];
			a = x[i + 3];

			t += '<div class="col-xs-12 col-sm-6 col-md-4 col-lg-4 thumb"><h3 class="zagolovok-d">' + h1 + '</h3><a href=' + n2 + ' data-fancybox="group" data-caption="' + h2 + '"><img src=' + n2 + ' alt="Фотография: ' + h1 + '" class="img-responsive"></a>';

			s = '';
			if (Array.isArray(a))
				for (k = 0; k < a.length; k++)
					s += this.vypusknikia(n1, k + 1, a[k]) + ' ';
			else
			if (a > 0)
				for (k = 1; k <= a; k++)
					s += this.vypusknikia(n1, k, h2) + ' ';
			if (s != '') t += '<p class="text-center">' + s + '</p>';

			t += '</div>' + this.kratnost32(j);
		}
		return t + '</div></div></div>';
	}

	novosti(m, z) {
		var i, q, n,
			t = '<div class="col-sm-12 col-md-6 col-md-offset-3"><div class="row displayflex">';

		for (i = 1; i <= m; i++) {
			q = ('0' + (i).toString()).slice(-2);
			n = this.imyafajla(q);
			t += '<div class="col-xs-12 col-sm-6 col-md-4 col-lg-4 thumb photo-container"><a href=' + n + ' data-fancybox="group"><img src=' + n + ' alt="Фотография ' + q + ': ' + z + '" class="img-responsive center-block"></a></div>' + this.kratnost32(i);
		}
		return t + '</div></div>';
	}
}

function tskripty() {}

tskripty.prototype = {

	header: function () {
		$('body').prepend($('<header>')
			.append($('<div>', {
					'class': 'container-fluid'
				})
				.append($('<div>', {
					'id': 'header-risunok-a'
				}))
				.append($('<div>', {
					'id': 'menyu-a'
				}))));
		$('#header-risunok-a').load('/header.html #header-x');
		$('#menyu-a').load('/header.html #menyu-b');
	},

	footer: function () {
		$('main').after($('<footer>').load('/footer.html'));
	},

	ciklovayakomissiyaprepodavateli: function (k, c) {
		var i, j, t, x, y, z;

		t = '<div class="row"><div class="col-md-6 col-md-offset-3 col-lg-6 col-lg-offset-3"><h1 class="zagolovok-a">' + k +
			'</h1></div></div><div class="row"><div class="col-md-3 col-lg-3"><p>Цикловые комиссии:</p><ul>';
		$.ajaxSetup({
			cache: false
		});
		x = $.ajax({
			'url': '/sveden/struct/ciklovyekomissii.txt',
			'async': false
		}).responseText.split('\r\n');
		for (i = 0; i < x.length; i++) {
			y = x[i].split(';');
			if (y[2] != k) t += '<li><a href="/sveden/struct/' + y[1] + '.html" target="_self">' + y[2] + '</a></li>';
		}

		t += '</ul></div><div class="col-md-6 col-lg-6"><table class="table table-condensed"><thead><tr><th class="text-center"></th><th class="text-center">Преподаватель</th><th class="text-center">Преподаваемые дисциплины</th></tr></thead><tbody>';
		x = $.ajax({
			'url': '/sveden/struct/prepodavateli.txt',
			'async': false
		}).responseText.split('\r\n');
		for (i = 0; i < x.length; i += 14)
			if (x[i + 13] == c) {
				t += '<tr itemprop="teachingStaff"><td rowspan="2"><img src="/sveden/struct/fotografii/' + x[i + 1] + '.jpg" alt="Фотография: ' + x[i] + '"></td><td>';

				switch (x[i + 12]) {
					case '1':
						t += '<p><strong>Заместитель председателя цикловой комиссии</strong></p>';
						break;
					case '2':
						t += '<p><strong>Председатель цикловой комиссии</strong></p>';
						break;
					case '3':
						t += '<p><strong>Председатель цикловой методической комиссии по стандартизации</strong></p>';
						break;
				}

				y = x[i].split(' ');
				switch (x[i + 2]) {
					case '1':
						z = 'Высшее';
						break;
					case '2':
						z = 'Среднее профессиональное';
						break;
				}
				
				t += '<p><strong><span itemprop="fio">' + y[0] + '<br>' + y[1] + ' ' + y[2] + '</span></strong></p><p><strong>Должность: </strong><span itemprop="post">' + x[i + 3] + 
				     '</span></p><p><strong><span itemprop="teachingLevel">' + z +'</span> образование по направлению: </strong><span itemprop="employeeQualification">' + x[i + 7] + 
					 '</span></p><p><strong>Квалификация: </strong><span itemprop="teachingQual">' + 
					 x[i + 9].replaceAll('$', ', ') + '</span></p>';

				if (x[i + 5] != '') t += '<p><strong>Ученая степень педагогического работника: </strong><span itemprop="degree">' + x[i + 5] + '</span></p>';
				if (x[i + 6] != '') t += '<p><strong>Ученое звание педагогического работника: </strong><span itemprop="academStat">' + x[i + 6] + '</span></p>';

				t += '<p><strong>Стаж работы общий (по специальности): </strong><span itemprop="genExperience">' + x[i + 10] + 
				     '</span> (<span itemprop="specExperience">' + x[i + 11] + 
					 '</span>)</p></td><td><div itemprop="teachingDiscipline"><ul class="text-justify"><li>' + 
				     x[i + 4].replaceAll('$', '</li><li>') + 
					 '</li></ul></div></td></tr><tr><td colspan="2"><p><strong>Повышение квалификации:</strong></p><div itemprop="profDevelopment"><ul class="text-justify"><li>' +
					 x[i + 8].replaceAll('$', '</li><li>') + 
					 '</li></ul></div></td></tr>';
			}
		return t + '</tbody></table></div></div>';
	},

	otdelysotrudniki: function (o, p) {
		var i, t, x, y;

		t = '<div class="row"><div class="col-md-6 col-md-offset-3 col-lg-6 col-lg-offset-3"><h1 class="zagolovok-a">' + o +
			'</h1></div></div><div class="row"><div class="col-md-3 col-lg-3"><ul>';
		$.ajaxSetup({
			cache: false
		});
		x = $.ajax({
			'url': '/sveden/struct/otdely.txt',
			'async': false
		}).responseText.split('\r\n');
		for (i = 0; i < x.length; i++) {
			y = x[i].split(';');
			if (y[2] != o) t += '<li><a href="/' + y[1] + '.html" target="_self"><span itemprop="Name">' + y[2] + '</span></a></li>';
		}

		t += '</ul></div><div class="col-md-6 col-lg-6"><table class="table table-condensed"><tbody>';
		x = $.ajax({
			'url': '/sveden/struct/sotrudniki.txt',
			'async': false
		}).responseText.split('\r\n');
		for (i = 0; i < x.length; i++) {
			y = x[i].split(';');
			if (y[0] == p) {
				t += '<tr><td><img src="/sveden/struct/fotografii/' + y[2] + '.jpg" alt="Фотография: ' + y[1] +
					'"></td><td><p class="fio"><span itemprop="Post">' + y[3] +
					'</span></p><p><strong><span itemprop="fio">' + y[1] + '</span></strong></p>';
                if (y[10] != '') t += '<p><strong>' + y[10] + '</strong></p>';
				if (y[4] != '') t += '<p><strong>Кабинет: </strong>' + y[4] + '</p>';
				if (y[5] != '' && y[6] != '') t += '<p><strong>' + y[5] + ': </strong>' + y[6] + '</p>';
				if (y[7] != '') t += '<p><strong>E-mail: </strong><a href="mailto:' + y[7] + '"><span itemprop="E-mail">' + y[7] + '</span></a></p>';
				t += '<p><strong>График работы: </strong>' + y[8] + '</p>';
				if (y[9] != '') t += '<p><strong>Прием по личным вопросам: </strong>' + y[9] + '</p>';
				t += '</td></tr>';
			}
		}
		return t + '</tbody></table></div></div></div>';
	},

	pokazattekst: function () {
		$('.pokazat-tekst').click(function () {
			if (!$(this).data('status')) {
				$(this).html('Скрыть...');
				$(this).data('status', true);
			} else {
				$(this).html('Показать полностью...');
				$(this).data('status', false);
			}
		});
	},

	top: function () {
		$('main').append($('<a>', {
				'id': 'top',
				'href': '#',
				'class': 'btn btn-primary btn-lg top',
				'role': 'button',
				'title': 'Вверх'
			})
			.append($('<span>', {
				'class': 'glyphicon glyphicon-chevron-up'
			})));

		$(window).scroll(function () {
			var x = $('#top')
			if ($(this).scrollTop() > 50)
				x.fadeIn();
			else
				x.fadeOut();
		});

		$('#top').click(function () {
			$('body, html').animate({
				scrollTop: 0
			}, 200);
			return false;
		});
	},

	novostib: function (d) {
		if (d === undefined || d == '') return undefined;
		var x = d.split('.');
		return new Date(x[2], x[1] - 1, x[0]);
	},

	novostia: function (dx, ds, de) {
		ds = skripty.novostib(ds);
		de = skripty.novostib(de);
		if (ds === undefined && de === undefined) return true;

		var x = dx.split('');
		dx = new Date('20' + x[0] + x[1], (x[2] + x[3]) - 1, x[4] + x[5]);

		if (ds === undefined) return dx <= de;
		if (de === undefined) return dx >= ds;
		return dx >= ds && dx <= de;
	},

	novosti: function (file, n, path, ds, de) {
	var a, i, f = !(n === undefined),
		k = 0,
		p, s = '',
		t = '';
	if (path != undefined) s = path + '/';
	$.ajaxSetup({
		cache: false
	});
	var x = $.ajax({
		'url': '/novosti/' + s + file + '.txt',
		'async': false
	}).responseText.split('\r\n');
	
	for (i = 0; i < x.length; i += 4)
		if (skripty.novostia(x[i], ds, de)) {
			p = '/novosti/' + s + x[i] + '/';
			a = '<a href="' + p + x[i] + '.html" target="_self">';
			// --- НАЧАЛО БЛОКА ОБРАБОТКИ ДАТЫ ---
			var dateHtml = '';
			var match = x[i].match(/^(\d{2})(\d{2})(\d{2})-(\d+)$/);
			var months = [
				"января", "февраля", "марта", "апреля", "мая", "июня", 
				"июля", "августа", "сентября", "октября", "ноября", "декабря"
			];
			if (match) {
				var year = "20" + match[1];
				/* var month = match[2]; */
				var day = parseInt(match[3], 10);;
				var monthText = months[parseInt(match[2], 10) - 1];
				dateHtml = '<p class="news-date-label">' + day + ' ' + monthText + ' ' + year + '</p>';
			}
			// --- КОНЕЦ БЛОКА ОБРАБОТКИ ДАТЫ ---
			t +=  '<a href="' + p + x[i] + '.html" target="_self"><div class="thumbnail thumbnail-container"><div class="img-news"><img src="' + p + 'original/' + x[i + 2] +
				'.jpg" class="novosti-risunok img-responsive" alt="Фотография: ' + x[i + 1] + '"</div><div class="caption caption-overlay"><h4>' + x[i + 1] +
				'</h4>' + dateHtml + '</div></div></div></a>';

			/* t +=  '<a href="' + p + x[i] + '.html" target="_self"><div class="row alert-news"><div class="col-xs-12 col-sm-6 col-md-6 col-lg-4 img-news"><img src="' + p + 'original/' + x[i + 2] +
			'.jpg" class="novosti-risunok img-responsive" alt="Фотография: ' + x[i + 1] + '"></div><div class="col-xs-12 col-sm-6 col-md-6 col-lg-8 text-news"><h2 class="zagolovok-d">' + x[i + 1] +
			'</h2><p class="novosti-tekst">' + x[i + 3] + '</p></div></div></a>' + dateHtml + '<hr>'; */
			
			k++;
			if (f && k == n+1) break;
		}
	return t;
},

	obyavleniya: function (v, n) {
		$.ajaxSetup({
			cache: false
		});
		var f = !(n === undefined),
			i, k = 0,
			t = '',
			x = $.ajax({
				'url': '/obyavleniya/obyavleniya.txt',
				'async': false
			}).responseText.split('\r\n');
		for (i = 0; i < x.length; i += 4)
			if (x[i + 1] != 0 && v == x[i + 2]) {
				t += '<div class="row">';
				if (k != 0)
					t += '<h2 class="zagolovok-b"></h2>';
				else
					t += '<h2></h2>';

				t += '<div class="novosti-tekst">' + x[i + 3] + '</div></div>';
				k++;
				if (f && k == n) break;
			}
		return t;
	},

	raspisanie: function () {
		$.ajaxSetup({
			cache: false
		});

		var a = $.ajax({
				'url': '/raspisanie/raspisanie.txt',
				'async': false
			}).responseText.split('\r\n'),
			f, i, j, n, pdf, t = '', z,
			x = [{
					title: 'Очная форма обучения',
					alt: 'Расписание занятий для очной формы обучения',
					suf: 's'
				},
				{
					title: 'Занятость преподавателей',
					alt: 'Расписание занятости преподавателей',
					suf: 'p'
				},
				{
					title: 'Заочная форма обучения',
					alt: 'Расписание занятий для заочной формы обучения',
					suf: 'z'
				}
			];

		for (i = 0; i < a.length - 1; i++) {
			t += '<div class="row"><div class="col-md-6 col-md-offset-3 col-lg-6 col-lg-offset-3"><h3 class="zagolovok-b">На ' + a[i] +
				'</h3></div></div><div class="row">';

			f = true;

			for (j = 0; j < x.length; j++) {
				t += '<div class="col-sm-4 col-md-2 col-lg-2';
				if (f) {
					t += ' col-md-offset-3 col-lg-offset-3';
					f = false;
				}

				n = a[i] + '_' + x[j].suf;
				pdf = n + '.pdf';

				$.ajax({
					'url': pdf,
					'async': false,
					'success': function () {
						z = '<a href="' + pdf + '" target="_blank" title="' + x[j].title + '"><img src="' + n +
							'.png" min-height="10vh" alt="' + x[j].alt + '"></a>';
					},
					'error': function () {
						z = '';
					}
				});

				t += '"><h3 class="zagolovok-d">' + x[j].title +'</h3><div class="thumbnail text-center"><div class="caption">' + z + '</div></div></div>';
			}
		}
		return t + '</div>';
	}
};

var skripty = new tskripty(),
	fotografii = new tfotografii();

$(function () {
	skripty.header();
	skripty.footer();
	skripty.top();
	skripty.pokazattekst();
	/* $('body').prepend('<div class="preloader"><div class="preloader__image"></div></div>'); */
});

window.onload = function () {
	$('head').append('<link rel="stylesheet" href="/vendors/bvi/dist/css/bvi.min.css" type="text/css">');
	$('body').append('<script src="/vendors/bvi/dist/js/bvi.min.js"></script><script>new isvek.Bvi();</script>');
	
	
	const dateYear = document.getElementById("date-field");
	if (dateYear) {
        dateYear.textContent = new Date().getFullYear();
    }

	/* document.body.classList.add('hide_preloader_animation');
	window.setTimeout(function () {
		document.body.classList.add('hide_preloader');
		document.body.classList.remove('hide_preloader_animation');
	}, 250); */

$(document).ready(function(){

 $('a[data-toggle="collapse"]').on('click', function(e) {
        e.preventDefault(); // Для предотвращения перехода по ссылке
        var target = $(this).attr('href');
        $(target).collapse('toggle');
    });

    // Предотвращение закрытия dropdown при клике внутри
    $('.dropdown-menu').on('click', function(event) {
        event.stopPropagation();
    });

	var owl = $('.owl-carousel');
	owl.owlCarousel({
		items:2,
		loop:true,
		margin:20,
		autoplay:true,
		center:true,
		autoplayTimeout:15000,
		autoplayHoverPause:true,
    	smartSpeed:800,
		navText: ["<svg width='25' height='25' viewBox='0 0 24 24' fill='#223c50'><path d='M16.67 0l2.83 2.829-9.339 9.175 9.339 9.167-2.83 2.829-12.17-11.996z'></path></svg>","<svg width='25' height='25' viewBox='0 0 24 24' fill='#223c50'><path d='M5 3l3.057-3 11.943 12-11.943 12-3.057-3 9-9z'></path></svg>"],
		responsiveClass:true,
		responsive:{
			0:{
				items:1,
				nav:true,
				loop:true
			},
			600:{
				items:1,
				nav:true,
				loop:true
			},
			1000:{
				items:1,
				nav:true,
				loop:true
			}
		}
	});	
});
}

document.addEventListener("DOMContentLoaded", function() {

/* КУКИ */

	fetch('/cookies/cookies.txt')
	.then(response => response.text())
	.then(htmlMarkup => {
		// Вставляет HTML-код прямо перед закрывающим тегом </body>
		document.body.insertAdjacentHTML('beforeend', htmlMarkup);

		const banner = document.getElementById("cookie-notice");
		const acceptBtn = document.getElementById("cookie-accept-btn");
		const leaveBtn = document.getElementById("cookie-leave-btn");

		// Ссылки для раскрытия текста
		const policyToggle = document.getElementById("cookie-policy-toggle");
		const detailedText = document.getElementById("cookie-detailed-text");

		// Проверяем, давал ли пользователь согласие ранее
		if (!localStorage.getItem("cookie_accepted")) {
			banner.style.display = "flex"; 
		}
		// ЛОГИКА РАСКРЫТИЯ ПЛАШКИ
		policyToggle.addEventListener("click", function(event) {
			event.preventDefault(); // Отменяем переход по ссылке #
        
        	// Переключаем видимость текста и класс анимации плашки
			if (detailedText.style.display === "none") {
				detailedText.style.display = "block";
				banner.classList.add("expanded");
			} else {
				detailedText.style.display = "none";
				banner.classList.remove("expanded");
			}
		});

		// Клик по кнопке «Принять»
		acceptBtn.addEventListener("click", function() {
			localStorage.setItem("cookie_accepted", "true"); 
			banner.style.display = "none"; 
		});

		// Клик по кнопке «Покинуть сайт»
		/* leaveBtn.addEventListener("click", function() { */
			// Уводим пользователя на главную Яндекса
		/*   window.location.href = "https://dzen.ru"; 
		}); */

	})
	.catch(error => console.error('Ошибка:', error));
	
/* КУКИ */

/* Citycard */
Citycard.init({ 
	providerId: '90717271',
	showContacts: true,
	showReceipt: true,
	type: 'button',
	buttonText: 'Оплатить онлайн',
	customCSS: "/vendors/citycard/css/widget.css", // или путь к вашему файлу CSS,
	referenceId: "b8c206dd-3b53-4b92-b18b-024027c14342"
});
/* Citycard */

});
