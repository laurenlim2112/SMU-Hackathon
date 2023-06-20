document.addEventListener('DOMContentLoaded', function() {

    document.querySelector('#in-progress-view').style.display = 'block';
    document.querySelector('#payment-pending-view').style.display = 'none';
    document.querySelector('#payment-received-view').style.display = 'none';

    document.querySelector('#in-progress').addEventListener('click', () => {
        document.querySelector('#in-progress-view').style.display = 'block';
        document.querySelector('#payment-pending-view').style.display = 'none';
        document.querySelector('#payment-received-view').style.display = 'none';
    });

    document.querySelector('#payment-pending').addEventListener('click', () => {
        document.querySelector('#in-progress-view').style.display = 'none';
        document.querySelector('#payment-pending-view').style.display = 'block';
        document.querySelector('#payment-received-view').style.display = 'none';
    });

    document.querySelector('#payment-received').addEventListener('click', () => {
        document.querySelector('#in-progress-view').style.display = 'none';
        document.querySelector('#payment-pending-view').style.display = 'none';
        document.querySelector('#payment-received-view').style.display = 'block';
    });
});