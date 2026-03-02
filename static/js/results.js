/**
 * 集計結果ページの制御
 */

const COLOR_BADGE_CLASS = {
    red:    'bg-danger',
    green:  'bg-success',
    blue:   'bg-primary',
    yellow: 'bg-warning text-dark'
};

const COLOR_LABEL = {
    red: '赤', green: '緑', blue: '青', yellow: '黄'
};

/**
 * liff.js から呼ばれる初期化関数
 */
function initResultsPage(user, shokudo) {
    document.getElementById('loading').classList.add('d-none');
    document.getElementById('results-app').classList.remove('d-none');

    const header = document.getElementById('shokudo-header');
    header.textContent = shokudo.shokudo_name;

    fetchResults(shokudo.shokudo_id);
}

/**
 * 集計データを取得して描画
 */
function fetchResults(shokudoId) {
    fetch(`/api/get-results?shokudoId=${encodeURIComponent(shokudoId)}`)
        .then(r => r.json())
        .then(data => {
            if (!data.success) {
                showError('データの取得に失敗しました');
                return;
            }
            renderResults(data.results);
        })
        .catch(() => showError('データの取得に失敗しました'));
}

/**
 * 全グループを描画
 */
function renderResults(results) {
    if (!results || results.length === 0) {
        document.getElementById('no-results').classList.remove('d-none');
        return;
    }

    const container = document.getElementById('results-container');
    results.forEach(group => {
        container.appendChild(buildResultCard(group));
    });
}

/**
 * 1開催日分のカードを生成
 */
function buildResultCard(group) {
    const { event_date, question, answers, colors, table } = group;

    // 列合計・総合計の計算
    const colorTotals = {};
    colors.forEach(c => { colorTotals[c.code] = 0; });
    answers.forEach(ans => {
        colors.forEach(c => {
            colorTotals[c.code] += (table[ans] && table[ans][c.code]) || 0;
        });
    });
    const grandTotal = Object.values(colorTotals).reduce((a, b) => a + b, 0);

    // カード要素を構築
    const card = document.createElement('div');
    card.className = 'card mb-3';

    // ヘッダー
    const cardHeader = document.createElement('div');
    cardHeader.className = 'card-header';
    const dateDiv = document.createElement('div');
    dateDiv.className = 'fw-bold';
    dateDiv.textContent = event_date;
    const questionDiv = document.createElement('div');
    questionDiv.className = 'small mt-1';
    questionDiv.textContent = question;
    cardHeader.appendChild(dateDiv);
    cardHeader.appendChild(questionDiv);

    // テーブル
    const cardBody = document.createElement('div');
    cardBody.className = 'card-body p-2';
    const tableWrapper = document.createElement('div');
    tableWrapper.className = 'table-responsive';

    const table_el = document.createElement('table');
    table_el.className = 'table table-sm table-bordered mb-0';

    // thead
    const thead = document.createElement('thead');
    thead.className = 'table-light';
    const headerRow = document.createElement('tr');

    // 空の左上セル
    const cornerTh = document.createElement('th');
    headerRow.appendChild(cornerTh);

    // 色列ヘッダー
    colors.forEach(c => {
        const th = document.createElement('th');
        th.className = 'text-center';
        const badge = document.createElement('span');
        badge.className = `badge ${COLOR_BADGE_CLASS[c.code] || 'bg-secondary'}`;
        badge.textContent = COLOR_LABEL[c.code] || c.code;
        const small = document.createElement('div');
        small.className = 'small mt-1';
        small.textContent = c.attribute;
        th.appendChild(badge);
        th.appendChild(small);
        headerRow.appendChild(th);
    });

    // 合計列ヘッダー
    const totalTh = document.createElement('th');
    totalTh.className = 'text-center';
    totalTh.textContent = '合計';
    headerRow.appendChild(totalTh);

    thead.appendChild(headerRow);

    // tbody
    const tbody = document.createElement('tbody');

    // 象限ごとの行
    answers.forEach(ans => {
        const rowTotal = colors.reduce(
            (sum, c) => sum + ((table[ans] && table[ans][c.code]) || 0), 0
        );
        const tr = document.createElement('tr');

        const labelTd = document.createElement('td');
        labelTd.innerHTML = '<strong>' + escapeHtml(ans) + '</strong>';
        tr.appendChild(labelTd);

        colors.forEach(c => {
            const td = document.createElement('td');
            td.className = 'text-center';
            td.textContent = (table[ans] && table[ans][c.code]) || 0;
            tr.appendChild(td);
        });

        const rowTotalTd = document.createElement('td');
        rowTotalTd.className = 'text-center';
        rowTotalTd.innerHTML = '<strong>' + rowTotal + '</strong>';
        tr.appendChild(rowTotalTd);

        tbody.appendChild(tr);
    });

    // 合計行
    const totalRow = document.createElement('tr');
    totalRow.className = 'table-secondary';
    const totalLabelTd = document.createElement('td');
    totalLabelTd.innerHTML = '<strong>合計</strong>';
    totalRow.appendChild(totalLabelTd);

    colors.forEach(c => {
        const td = document.createElement('td');
        td.className = 'text-center';
        td.innerHTML = '<strong>' + colorTotals[c.code] + '</strong>';
        totalRow.appendChild(td);
    });

    const grandTotalTd = document.createElement('td');
    grandTotalTd.className = 'text-center';
    grandTotalTd.innerHTML = '<strong>' + grandTotal + '</strong>';
    totalRow.appendChild(grandTotalTd);
    tbody.appendChild(totalRow);

    table_el.appendChild(thead);
    table_el.appendChild(tbody);
    tableWrapper.appendChild(table_el);
    cardBody.appendChild(tableWrapper);

    card.appendChild(cardHeader);
    card.appendChild(cardBody);
    return card;
}

/**
 * HTML エスケープ
 */
function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
