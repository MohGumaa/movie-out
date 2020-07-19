$(document).ready(() => {
    $('#searchForm').on('submit', e => {
        let searchText = $('#searchText').val();
        if(searchText === ''){
            // console.log('enter');
            $('#movies').html(
                `
                <div class="alert alert-danger m-auto" role="alert">
                    Please Enter Movie Name!
                </div>

                `);
        } else {
            getMovies(searchText);
        }
        e.preventDefault();
    });
});

function getMovies(searchText){
    axios.get('http://www.omdbapi.com/?apikey=d5bccb42&s='+searchText)
        .then(response => {
            let movies = response.data.Search;
            showList = response.data.Response;
            let output = '';
            if (showList === 'False'){
                output = `
                <div class="alert alert-warning m-auto" role="alert">
                    Please Provide other Name for Searching!
                </div>
                `;
            } else {

                $.each(movies, (index, movie) =>{
                    output += `
                    <div class="col-md-3">
                      <div class="card text-center mb-5">
                        <img class="card-img-top" src="${movie.Poster}" alt="Card image cap">
                        <div class="card-body text-white bg-secondary ">
                            <p class="card-text">${movie.Title}</p>
                            <a href="/movie/${movie.imdbID}" class="btn btn-primary">More Details</a>
                        </div>
                      </div>
                    </div>
                    `;
                });
            }

            $('#movies').html(output)
        })
        .catch((error => console.log(error)));
}