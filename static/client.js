document.addEventListener('DOMContentLoaded', function() {

    document.querySelector('#in-progress-view').style.display = 'block';
    document.querySelector('#payment-pending-view').style.display = 'none';
    document.querySelector('#payment-received-view').style.display = 'none';
    document.querySelector('#select-timesheet').style.display = 'none';

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

    document.querySelector('#addNewTimesheetModalOpen').addEventListener('click', () => {
        var modal = document.querySelector('#addNewTimesheetModal');
        var backdrop = document.querySelector('#addNewTimesheetModalBackdrop');
        backdrop.style.display = 'flex';
        modal.style.display = 'flex';
    })

    document.querySelectorAll('.addNewTimesheetModalClose').forEach((item) => {
        item.addEventListener('click', () => {
            var modal = document.querySelector('#addNewTimesheetModal')
            var backdrop = document.querySelector('#addNewTimesheetModalBackdrop');
            backdrop.style.display = 'none';
            modal.style.display = 'none';
        })
    })

    document.querySelector('#billFixedFeeModalOpen').addEventListener('click', () => {
        var modal = document.querySelector('#billFixedFeeModal');
        var backdrop = document.querySelector('#billFixedFeeModalBackdrop');
        backdrop.style.display = 'flex';
        modal.style.display = 'flex';
    })

    document.querySelectorAll('.billFixedFeeModalClose').forEach((item) => {
        item.addEventListener('click', () => {
            var modal = document.querySelector('#billFixedFeeModal')
            var backdrop = document.querySelector('#billFixedFeeModalBackdrop');
            backdrop.style.display = 'none';
            modal.style.display = 'none';
        })
    })

    document.querySelector('#importExcelModalOpen').addEventListener('click', () => {
        var modal = document.querySelector('#importExcelModal');
        var backdrop = document.querySelector('#importExcelModalBackdrop');
        backdrop.style.display = 'flex';
        modal.style.display = 'flex';
    })

    document.querySelectorAll('.importExcelModalClose').forEach((item) => {
        item.addEventListener('click', () => {
            var modal = document.querySelector('#importExcelModal')
            var backdrop = document.querySelector('#importExcelModalBackdrop');
            backdrop.style.display = 'none';
            modal.style.display = 'none';
        })
    })

    document.querySelector('#addNewLawyerModalOpen').addEventListener('click', () => {
        var modal = document.querySelector('#addNewLawyerModal');
        var backdrop = document.querySelector('#addNewLawyerModalBackdrop');
        backdrop.style.display = 'flex';
        modal.style.display = 'flex';
    })

    document.querySelectorAll('.addNewLawyerModalClose').forEach((item) => {
        item.addEventListener('click', () => {
            var modal = document.querySelector('#addNewLawyerModal')
            var backdrop = document.querySelector('#addNewLawyerModalBackdrop');
            backdrop.style.display = 'none';
            modal.style.display = 'none';
        })
    })

    var checkbox = document.getElementById('addtotimesheet')
    checkbox.onclick = function() {
        if (checkbox.checked) {
            document.querySelector('#select-timesheet').style.display = 'block';
        } else {
            document.querySelector('#select-timesheet').style.display = 'none';
        }
    }
});