document.addEventListener('DOMContentLoaded', function() {

    if (document.querySelector('#start-task-view') != null) {
        document.querySelector('#start-task-view').style.display = 'block';
        document.querySelector('#end-task-view').style.display = 'none';

        document.querySelector('#confirm-start').addEventListener('click', () => start_task());

        document.querySelectorAll('.submitTaskModalOpen').forEach((item) => {
            item.addEventListener('click', () => {
                var modal = document.querySelector('#submitTaskModal');
                var backdrop = document.querySelector('#submitTaskModalBackdrop');
                backdrop.style.display = 'flex';
                modal.style.display = 'flex';
            })
        })

        document.querySelectorAll('.submitTaskModalClose').forEach((item) => {
            item.addEventListener('click', () => {
                var modal = document.querySelector('#submitTaskModal')
                var backdrop = document.querySelector('#submitTaskModalBackdrop');
                backdrop.style.display = 'none';
                modal.style.display = 'none';
            })
        })

        document.querySelector('#addDisbursementModalOpen').addEventListener('click', () => {
            var modal = document.querySelector('#addDisbursementModal');
            var backdrop = document.querySelector('#addDisbursementModalBackdrop');
            backdrop.style.display = 'flex';
            modal.style.display = 'flex';
        })

        document.querySelectorAll('.addDisbursementModalClose').forEach((item) => {
            item.addEventListener('click', () => {
                var modal = document.querySelector('#addDisbursementModal')
                var backdrop = document.querySelector('#addDisbursementModalBackdrop');
                backdrop.style.display = 'none';
                modal.style.display = 'none';
            })
        })

        document.querySelector('#generateInvoiceModalOpen').addEventListener('click', () => {
            var modal = document.querySelector('#generateInvoiceModal');
            var backdrop = document.querySelector('#generateInvoiceModalBackdrop');
            backdrop.style.display = 'flex';
            modal.style.display = 'flex';
        })

        document.querySelectorAll('.generateInvoiceModalClose').forEach((item) => {
            item.addEventListener('click', () => {
                var modal = document.querySelector('#generateInvoiceModal')
                var backdrop = document.querySelector('#generateInvoiceModalBackdrop');
                backdrop.style.display = 'none';
                modal.style.display = 'none';
            })
        })
    }

    if (document.querySelector('#markAsPaidModalOpen') != null) {
        document.querySelector('#markAsPaidModalOpen').addEventListener('click', () => {
            var modal = document.querySelector('#markAsPaidModal');
            var backdrop = document.querySelector('#markAsPaidModalBackdrop');
            backdrop.style.display = 'flex';
            modal.style.display = 'flex';
        })
    
        document.querySelectorAll('.markAsPaidModalClose').forEach((item) => {
            item.addEventListener('click', () => {
                var modal = document.querySelector('#markAsPaidModal')
                var backdrop = document.querySelector('#markAsPaidModalBackdrop');
                backdrop.style.display = 'none';
                modal.style.display = 'none';
            })
        })
    }
});

function start_task() {
    document.querySelector('#start-task-view').style.display = 'none';
    document.querySelector('#end-task-view').style.display = 'block';
    start = Date.now();
    const date = new Date();
    day = date.getDate();
    month = date.getMonth() + 1;
    year = date.getFullYear();
    currentDate = `${day}-${month}-${year}`;
    timesheet = location.pathname.split('/')[2];
    document.querySelector('#confirm-end').addEventListener('click', () => end_task());
    function end_task() {
        end = Date.now();
        duration = end - start;
        document.querySelector('#task-submit').addEventListener('click', () => submit_task(timesheet));
        function submit_task(timesheet) {
            fetch(`/addtask/${timesheet}`, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    date: currentDate,
                    hours: (duration / 3600000).toFixed(1),
                    rate: document.querySelector('#hourly-rate').value,
                    description: document.querySelector('#task-description').value
                })
            })
            .catch(error => console.log(error));
            document.querySelector('#start-task-view').style.display = 'block';
            document.querySelector('#end-task-view').style.display = 'none';
        }
    }
}