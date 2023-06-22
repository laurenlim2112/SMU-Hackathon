document.addEventListener('DOMContentLoaded', function() {

    document.querySelector('#addClientModalOpen').addEventListener('click', () => {
        var modal = document.querySelector('#addClientModal');
        var backdrop = document.querySelector('#addClientModalBackdrop');
        backdrop.style.display = 'flex';
        modal.style.display = 'flex';
    })

    document.querySelectorAll('.addClientModalClose').forEach((item) => {
        item.addEventListener('click', () => {
            var modal = document.querySelector('#addClientModal')
            var backdrop = document.querySelector('#addClientModalBackdrop');
            backdrop.style.display = 'none';
            modal.style.display = 'none';
        })
    })

    document.querySelector('#newFixedFeeModalOpen').addEventListener('click', () => {
        var modal = document.querySelector('#newFixedFeeModal');
        var backdrop = document.querySelector('#newFixedFeeModalBackdrop');
        backdrop.style.display = 'flex';
        modal.style.display = 'flex';
    })

    document.querySelectorAll('.newFixedFeeModalClose').forEach((item) => {
        item.addEventListener('click', () => {
            var modal = document.querySelector('#newFixedFeeModal')
            var backdrop = document.querySelector('#newFixedFeeModalBackdrop');
            backdrop.style.display = 'none';
            modal.style.display = 'none';
        })
    })
})