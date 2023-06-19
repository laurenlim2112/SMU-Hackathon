document.addEventListener('DOMContentLoaded', function() {

    document.querySelector('#end-task-view').style.display = 'none';

    document.querySelector('#confirm-start').addEventListener('click', () => start_task());

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
    id = location.pathname.split('/')[2];
    document.querySelector('#confirm-end').addEventListener('click', () => end_task());
    function end_task() {
        end = Date.now();
        duration = end - start;
        document.querySelector('#task-submit').addEventListener('click', () => submit_task(id));
        function submit_task(id) {
            fetch(`/addtask/${id}`, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    date: currentDate,
                    hours: duration / 3600000,
                    description: document.querySelector('#task-description').value
                })
            })
            .catch(error => console.log(error));
            document.querySelector('#start-task-view').style.display = 'block';
            document.querySelector('#end-task-view').style.display = 'none';
        }
    }
}