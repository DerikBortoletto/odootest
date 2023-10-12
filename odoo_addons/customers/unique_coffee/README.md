Utilização

Este controller possui a rota:
Rota GET /contacts/new

Esta rota é responsável por renderizar o formulário de criação de contatos. Para
utilizá-la, basta acessar a URL http://localhost:8069/contacts/new em seu
navegador.
Rota POST /contacts/create

Esta rota é responsável por receber os dados enviados pelo formulário de criação
de contatos e criar um novo contato no banco de dados. Para utilizá-la, você
precisará enviar um request POST contendo os seguintes parâmetros:

    Fullname: nome do contato (obrigatório)
    phoneNumber: número de telefone do contato (obrigatório)
    birthdate: data de nascimento do contato (obrigatório)

Caso algum dos parâmetros obrigatórios não seja enviado ou o formato de data
seja inválido, o controller retornará uma mensagem de erro.

Em caso de sucesso, o controller criará um novo registro na tabela de contatos e
retornará uma mensagem de sucesso.
Autor

Este controller foi criado por Johnatna Souza.