const { validateUserId } = require('./validators');

class UserController {
    constructor({ userModel }) {
        this.userModel = userModel;
    }

    async remove(rawId) {
        await this.userModel.deleteById(validateUserId(rawId));
        return 'Usuário deletado com suas matrículas e pagamentos.';
    }
}

module.exports = UserController;
