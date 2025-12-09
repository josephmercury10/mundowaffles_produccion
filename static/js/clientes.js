/* JavaScript para el mantenedor de Clientes */

$(document).ready(function() {
    // Inicializar DataTable con configuración en español
    var table = $('#datatablesSimple').DataTable({
        language: {
            processing: "Procesando...",
            search: "Buscar:",
            lengthMenu: "Mostrar _MENU_ registros",
            info: "Mostrando _START_ a _END_ de _TOTAL_ clientes",
            infoEmpty: "No hay clientes para mostrar",
            infoFiltered: "(filtrado de _MAX_ registros totales)",
            loadingRecords: "Cargando...",
            zeroRecords: "No se encontraron clientes",
            emptyTable: "No hay clientes registrados",
            paginate: {
                first: "Primero",
                previous: "<i class='fas fa-chevron-left'></i>",
                next: "<i class='fas fa-chevron-right'></i>",
                last: "Último"
            }
        },
        pageLength: 10,
        lengthChange: false,
        searching: true,
        ordering: true,
        order: [[0, 'asc']], // Ordenar por nombre
        dom: 'rtip', // Ocultar búsqueda por defecto (usamos la nuestra)
        columnDefs: [
            { orderable: false, targets: 5 } // Desactivar ordenación en Acciones
        ]
    });

    // Aplicar filtro de estado "Activo" por defecto
    table.column(4).search('^Activo$', true, false).draw();
    actualizarContador();

    // Búsqueda personalizada (global)
    $('#searchBox').on('keyup', function() {
        table.search(this.value).draw();
        actualizarContador();
    });

    // Filtro por estado (columna 4)
    $('#filterEstado').on('change', function() {
        var val = this.value;
        if (val) {
            table.column(4).search('^' + val + '$', true, false).draw();
        } else {
            table.column(4).search('').draw();
        }
        actualizarContador();
    });

    // Filtro por tipo de persona (columna 3)
    $('#filterTipo').on('change', function() {
        var val = this.value;
        if (val) {
            table.column(3).search('^' + val + '$', true, false).draw();
        } else {
            table.column(3).search('').draw();
        }
        actualizarContador();
    });

    // Cambiar cantidad de registros por página
    $('#pageLength').on('change', function() {
        table.page.len(parseInt(this.value)).draw();
    });

    // Limpiar todos los filtros
    $('#clearFilters').on('click', function() {
        $('#searchBox').val('');
        $('#filterEstado').val('');
        $('#filterTipo').val('');
        $('#pageLength').val('10');
        table.search('');
        table.columns().search('');
        table.page.len(10).draw();
        actualizarContador();
    });

    // Función para actualizar contador de registros filtrados
    function actualizarContador() {
        var info = table.page.info();
        var filteredCount = info.recordsDisplay;
        var totalCount = info.recordsTotal;
        if (filteredCount === totalCount) {
            $('#totalRegistros').text(totalCount + ' registros');
        } else {
            $('#totalRegistros').text(filteredCount + ' de ' + totalCount + ' registros');
        }
    }
});
